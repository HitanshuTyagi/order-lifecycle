order-lifecycle/
│
├── app/
│   ├── main.py                         # FastAPI entry point
│   │
│   ├── core/                           # Shared application infrastructure
│   │   ├── config.py                   # Environment/configuration
│   │   ├── database.py                 # MongoDB connection
│   │   ├── enums.py                    # Shared order statuses
│   │   └── exceptions.py               # Common application errors
│   │
│   ├── orders/                         # Person A: order lifecycle start
│   │   ├── routes.py                   # Create/get order APIs
│   │   ├── service.py                  # Order business logic
│   │   ├── repository.py               # Order MongoDB operations
│   │   ├── schemas.py                  # Request/response models
│   │   └── validators.py               # Application-level validation
│   │
│   ├── packing/                        # Person A: picker workflow
│   │   ├── routes.py                   # Picker APIs
│   │   ├── service.py                  # Packing business rules
│   │   └── repository.py               # Atomic packing DB operations
│   │
│   ├── delivery/                       # Person B: rider workflow
│   │   ├── routes.py                   # Rider/delivery APIs
│   │   ├── service.py                  # Delivery/idempotency logic
│   │   └── repository.py               # Delivery DB operations
│   │
│   ├── reporting/                      # Person C: daily report
│   │   ├── routes.py                   # Report API
│   │   ├── service.py                  # Timezone/report logic
│   │   └── repository.py               # Efficient report queries
│   │
│   └── batching/                       # Person C: Day 2
│       ├── routes.py                   # Batch APIs
│       ├── service.py                  # Batching algorithm
│       └── repository.py               # Orders/config DB access
│
├── tests/
│   ├── integration/                    # Real HTTP endpoint tests
│   │   ├── test_orders.py
│   │   ├── test_packing.py
│   │   ├── test_delivery.py
│   │   └── test_reporting.py
│   │
│   ├── concurrency/                    # Race-condition tests
│   │   └── test_packing_concurrency.py
│   │
│   ├── legacy/                         # Old-document compatibility tests
│   │   └── test_legacy_orders.py
│   │
│   └── fixtures/                       # Reusable test data
│       └── seed_data.py
│
├── scripts/
│   ├── setup_db.py                     # Collections/indexes/validators
│   └── seed_db.py                      # Development seed data
│
├── .github/
│   └── workflows/
│       └── ci.yml                      # Run tests automatically in PRs
│
├── .env.example                        # Required environment variables
├── .gitignore                          # Files Git should ignore
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Backend container definition
├── docker-compose.yml                  # Backend + MongoDB local setup
├── pytest.ini                           # Test configuration
└── README.md                           # Project documentation