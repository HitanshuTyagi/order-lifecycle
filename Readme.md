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
│   ├── test_legacy_order_read.py                    
│
│
├── .env.example                        # Required environment variables
├── .gitignore                          # Files Git should ignore
├── requirements.txt                    # Python dependencies
├── pytest.ini                           # Test configuration
└── README.md                           # Project documentation



To create the venv environment- .\venv\Scripts\Activate.ps1 
To start the project- uvicorn app.main:app --reload    