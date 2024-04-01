
# Elasticsearch with Django Rest Framework

## Steps to run using docker
1. ### Create a virtual environment
``` python3 -m virtualenv venv ```

2. ### Bring up the dockerized services
```docker-compose up --build``` 

This is the docker-compose.yml file:
```
version: '3.8'

services:
  es:
      image: docker.elastic.co/elasticsearch/elasticsearch:7.11.0
      environment:
        - discovery.type=single-node
        - xpack.security.enabled=false
        - cluster.name=es
      ports:
      - "9200:9200"

  web:
      build: .
      command: >
        sh -c "python manage.py migrate &&
              python manage.py runserver 0.0.0.0:8000"
      volumes:
        - .:/usr/src/app/
      ports:
        - 8000:8000
      env_file:
        - docker-compose.env
      depends_on:
        - es
```

This creates two different containers, the container es(Elasticsearch) pulls the Elasticsearch image from Docker Hub and runs on the port 9200 and the container web builds container from the Dockerfile in the root folder, and runs required migrations and starts the server.

3. ### Populate database

```docker-compose exec web python manage.py populate_db```

This command populates user, category and articles using factory_boy and faker.

4. ### Build index for the data in the database

```docker-compose exec web python manage.py create_index  --rebuild```

This command builds index for every single row and every single token(word) in the database. But what actually is an index in Elasticsearch? I'll explain after we run the project.

5. ### Goto localhost:8000

Here you can see 3 different api endpoints: admin, blog and search.
  
blog - The blog endpoint contains 3 different endpoints, /users/, /categories/, and /articles/ that are used to list the corresponding users, article categories and articles. Click on any one endpoint and see what it returns.
  
search - Now this is what we're interested in. If you go to the search endpoint, you can see 3 different endpoints where you can send a query and it returns corresponding data if it finds anything in the database.
  
You saw how the data that matched the search query got returned, but how does elasticsearch actually work and why should we use it?

## Without docker
If you don't want to use docker, you have to manually install elasticsearch and run on port 9200.


# ElasticSearch

_You know, for search (and analysis)_

Elasticsearch is the distributed search and analytics engine built on Apache Lucene and developed in Java. Elasticsearch allows you to store, search, and analyze huge volumes of data quickly and in near real-time and give back answers in milliseconds. It’s able to achieve fast search responses because instead of searching the text directly, it searches an index. It uses a structure based on documents instead of tables and schemas and comes with extensive REST APIs for storing and searching the data. At its core, you can think of Elasticsearch as a server that can process JSON requests and give you back JSON data.

Let's understand how elasticsearch works using Users table in our project's example.

i. You migrate all your django models to your database and populate the rows using factory-boy. Now you database is ready for indexing.

ii. When you run the search_index command, it maps each row in a table to corresponding document and groups them into an index.

![search_index](https://github.com/SaugatGhimire321/drf-elasticsearch/assets/96584301/12a26426-e321-4ab4-ab5c-aa94b5fd6716)

Here, it mapped 20 articles, 5 categories and 10 users to their corresponding indexes as documents. Whenever new row gets added, the indexes are also automatically updated.

![map_documents](https://github.com/SaugatGhimire321/drf-elasticsearch/assets/96584301/b1e35d0b-51a2-44e5-9e9e-1961b84de821)

It also creates an ***Inverted Index*** for every token(word) in the database

![inverted_index](https://github.com/SaugatGhimire321/drf-elasticsearch/assets/96584301/e15b6dca-4769-4846-a9b7-67154acd4fd0)

When we search for a word, let's say "Indeed", it does not search through the whole document, rather it checks the reverse index and performs operations only on the documents that the token exists in. That's why elastic search is blazingly fast!

But how did search_index command actually work? 

If we go to documents.py file in blog app, you can see that we registered a document class that maps the specified model to the corresponding index.

![userdocument](https://github.com/SaugatGhimire321/drf-elasticsearch/assets/96584301/2541f0aa-64ae-418b-8005-caa939519f6d)

Here I created two classes inside the UserDocument class, Django class contains which model to use, what are the fields that should be indexed, and Index class contains name of the index and some settings related to the index.

But wait, what are shards and replicas?

### Shards

The index that was created from the table, that is a shard! The number of shards determine across how many shards we want to distribute our data.

Why do we need to create multiple number of shards?

See, it's okay when you see no exponential growth in your data to have 1 shard like our example. But what if you data is growing exponentially and let's say you have more than 1 million data on which you have to search? Distributing your data across multiple shards across multiple nodes can help in parallely processing your data and give you faster results.

### Replicas

Replicas are exact copies of shards that are to increase search performance and for fail-over. If in case, one shard fails or goes down, Elasticsearch can switch to the replica shard and continue its process.

Now how does the search actually work?

In search/urls.py, 

``` from django.urls import path

from apps.search.views import SearchArticles, SearchCategories, SearchUsers

urlpatterns = [
    path("user/<str:query>/", SearchUsers.as_view()),
    path("category/<str:query>/", SearchCategories.as_view()),
    path("article/<str:query>/", SearchArticles.as_view()),
]
```

When we send any word or phrase we want to query, it goes to the corresponding view in search/views.py,

```
class SearchUsers(PaginatedElasticSearchAPIView):
    serializer_class = UserSerializer
    document_class = UserDocument

    def generate_q_expression(self, query):
        return Q("bool",
                 should=[
                     Q("match", username=query),
                     Q("match", first_name=query),
                     Q("match", last_name=query),
                 ], minimum_should_match=1)
```

Inside generate_q_expression, we see a elasticsearch query, which checks if username, or first_name or last_name ***exactly*** matches the query we sent, it returns True only if at least one condition (match in username, first_name, or last_name) is met.

Note that the actual query looks very different if we try to execute the query directly in the Kibana console. The query inside Q is made pythonic which at last gets mapped to the low level query.

But where do we use this function? See the PaginatedElasticSearchAPIView that we inhertied in SearchUsers class?

```
class PaginatedElasticSearchAPIView(APIView, LimitOffsetPagination):
    serializer_class = None
    document_class = None

    @abc.abstractmethod
    def generate_q_expression(self, query):
        """
            This method should be overridden and return a Q() expression
        """
    
    def get(self, request, query):
        try:
            q = self.generate_q_expression(query)
            search = self.document_class.search().query(q)
            response = search.execute()

            print(f'Found {response.hits.total.value} hits for query: {query}')

            results = self.paginate_queryset(response, request, view=self)
            serializer = self.serializer_class(results, many=True)
            return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            return HttpResponse(e, status=500)
```

Let's see with an example.

When you go to the api endpoint

```http://localhost:8000/search/user/kenneth/```

The get method of PaginatedElasticSearchAPIView gets called, and since SearchUsers class is instantiated,

``` q = self.generate_q_expression(query) ```

The implementation of generate_q_expression in SearchUsers class gets called, which is executed and paginated and the corresponding result is shown.

![searchusers](https://github.com/SaugatGhimire321/drf-elasticsearch/assets/96584301/696f192d-7cc4-4ebb-8466-f9eed778d8cd)


let's see another view SearchArticles,

```
class SearchArticles(PaginatedElasticSearchAPIView):
    serializer_class = ArticleSerializer
    document_class = ArticleDocument

    def generate_q_expression(self, query):
        return Q(
                "multi_match", query=query,
                fields=[
                    "title",
                    "author",
                    "type",
                    "content"
                ], fuzziness="auto")
```

This query is also similar to the above SearchUsers query, but it has a fuzziness attribute, which allows for some tolerance for typos or misspellings in the search term. "auto" setting lets the search engine choose the most appropriate level of fuzziness.

For example, if I search hit this api endpoint,

``` GET /search/article/indeod/ ```

This query can tolerate some level of typo and can still get search results for data matching 'indeed'.

![indeed](https://github.com/SaugatGhimire321/drf-elasticsearch/assets/96584301/b5035c9d-eaa0-4c00-8ef5-9292e90c303b)

This is only a basic implementation of ElasticSearch locally and it does not cover scalability and analysis part.
To learn more about ElasticSearch queries and how the ELK Stack works, check out https://elastic.co

