# Catalog

### How to Run

```sh
$ python create_db.py
```

```sh
$ python application.py
```

### API

1. View all categories and items
* http://localhost:8000/json

2. View individual category with category_id
* http://localhost:8000/category/<int:category_id>/json

3. View individual item with item_id
* http://localhost:8000/category/<int:category_id>/<int:item_id>/json
