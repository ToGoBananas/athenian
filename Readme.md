# Env setup

```shell
docker compose up -d
```

We need to wait about 30 seconds after this command (Singlestore setup, migrations, fill DB with test data) 
You can view Swagger at `http://127.0.0.1:8001/core/public/v1/docs`

# Local env setup:
- Install python 3.11
- Install poetry

```shell
poetry install
```


# Assumptions

To make the coding challenge simpler, I've made several assumptions:
- Snapshots and products are immutable
- Image filename unique per snapshots
- QA is not going to use multiple browser tabs/devices simultaneously
- Product has one image

# Other comments

- I've decided to use SingleStore as a database because it has many cool features for ML/CV projects, and I've always wanted to try it :)
- Consistency is going to be enforced on the application side
- SingleStore might not be the best choice cause of poor integration with the python ecosystem
- The images are going to be stored in S3 storage (minio)
- Application has no auth system (you pass username as a header to every request)

# Areas of improvement

- Concurrency
- Generalization
- Health-checks
- Migrations (it might be possible to use alembic)
- Transactions and overall consistency
- Query optimization?

# Bonus

### Tests

With SingleStore, it is pretty hard to implement proper testing (because there are no batteries). But I've done some quick and dirty testing (without database cleanup).
It can be run with the command:

```shell
pytest
```

### Formulate ideas to reduce QA-time while maintaining the same accuracy.

1. I would like to implement web page control with hotkeys (← for approve, → to disapprove snapshots). It can significantly increase speed for PC users.
2. It might be a good idea to show multiple images of some products (helps to distinguish similar products).
3. To make the application even more responsive (to increase QA speed), after the snapshot is approved frontend app can show the following snapshot without waiting for the server response.
4. Maybe QA makes mistakes after product change? Then we could show some notifications on the product switch (+show snapshots of the same product in a row).