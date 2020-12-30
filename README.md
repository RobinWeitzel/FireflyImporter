# Firefly importer
A FinTS based importer for [FireflyIII](https://www.firefly-iii.org/)

### Requirements
* A server with docker installed

### Installation
```
docker run robinweitzel/firefly_importer -e BANK_BLZ <your blz> -e BANK_USERNAME <your username> -e BANK_PIN <your pin> -e BANK_URL <your url> -e BANK_PRODUCT_ID <your product id> -e FIREFLY_URL <your url> -e FIREFLY_TOKEN <your personal token>
```