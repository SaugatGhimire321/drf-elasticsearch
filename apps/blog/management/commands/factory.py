import factory
import random
from django.contrib.auth.models import User
from apps.blog.models import Category, Article, ARTICLE_TYPES

from factory.faker import faker

FAKE = faker.Faker()

def get_type():
    choices = [x[0] for x in ARTICLE_TYPES]
    return random.choice(choices)

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: "user_%d" % (n+1))
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = "helloworld"


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
    
    name = factory.Sequence(lambda n: "category_%d" % (n+1))
    description = factory.Faker("sentence", nb_words=6)


class ArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Article
    
    title = factory.Faker("sentence", nb_words=12)
    author = factory.Iterator(User.objects.all())
    type = factory.LazyFunction(get_type)

    @factory.lazy_attribute
    def content(self):
        x = ""
        for _ in range(0,5):
            x += "\n" + FAKE.paragraph(nb_sentences=30)+ "\n"
        return x
    
    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
        # If categories are explicitly provided, use them.
            for category in extracted:
                self.categories.add(category)
        
        all_categories = list(Category.objects.all())
        if all_categories:
            num_categories = random.randint(1, 3)
            random_categories = random.sample(all_categories, num_categories)
            for category in random_categories:
                self.categories.add(category)
    
