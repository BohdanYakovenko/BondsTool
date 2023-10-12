# Analytic BondsTool


## Table of Contents
[English]

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Custom Logo (Optional)](#custom-logo-optional)
- [Deployment (Optional)](#deployment-optional)

---
[Українська]

- [Опис](#опис)
- [Завантаження](#завантаження)
- [Використання](#використання)
- [Додати лого (необов'язково)](#додати-лого-необовязково)
- [Розгортання на сервері (необов'язково)](#розгортання-на-сервері-необовязково)

## Introduction

The Analytic BondsTool is a web service that helps manage and analyse the trading of governmental bonds in Ukraine, based on the database of [NBU (The National Bank of Ukraine)](https://bank.gov.ua/en/markets/ovdp) and the weekly auction announcement made by [The Ministry of Finance Of Ukraine](https://mof.gov.ua/en/ogoloshennja-ta-rezultati-aukcioniv).

It allows the user to interactively compare bonds and download the analytics to Excel format afterward for further analysis.


## Installation

To install and run the BondsTool, follow these steps:


1. Clone the GitHub repository
```bash
git clone https://github.com/BohdanYakovenko/BondsTool.git
```

2. Change your current directory to the BondsTool project directory
```bash
cd BondsTool
```

3. Create a Python virtual environment
```bash
python -m venv myenv
```

4. Activate the virtual environment (commands may vary by operating system):

* On Windows
    ```bash
    myenv\Scripts\activate
    ```

* On macOS and Linux
    ```bash
    source myenv/bin/activate
    ```


5. Install the BondsTool package
```bash
pip install .
```

6. Run the BondsTool application
```bash
python src/bondstool/app.py
```

## Usage

The run command will provide a url address by which the application will be available

By default, the program will display an analysis of a manually created example file. To process your data, use the button under the title to download your file in the correct format.

Use the default file as an example of the format required. It is located in [`BondsTool/assets/example_bag.xlsx`](BondsTool/assets/example_bag.xlsx).


## Custom Logo (Optional)

To upload the company's logo to the web page, the file with the logo image should be saved into the directory [`BondsTool/assets`](BondsTool/assets) on your device with the name `logo.png`.


## Deployment (Optional)

To deploy the application to the server:

* On Windows
    ```bash
    waitress-serve --listen=*:8050 src.bondstool.app:server
    ```

* On macOS and Linux
    ```bash
    gunicorn src.bondstool.app:server -b :8050
    ```

---
## Опис

Analytic BondsTool — це веб-сервіс, який допомагає керувати та аналізувати покупку державних облігацій в Україні на основі бази даних  [НБУ (Національного банку України)](https://bank.gov.ua/en/markets/ovdp) та щотижневого аукціону, який публікує [Міністерство фінансів України](https://mof.gov.ua/en/ogoloshennja-ta-rezultati-aukcioniv).

Це дозволяє користувачеві інтерактивно порівнювати облігації та завантажувати аналітику у формат Excel для подальшого аналізу.


## Завантаження

Щоб установити та запустити BondsTool, виконайте наступні дії:


1. Клонуйте репозиторій GitHub
```bash
git clone https://github.com/BohdanYakovenko/BondsTool.git
```

2. Змініть свою поточну директорію на директорію проекту BondsTool

```bash
cd BondsTool
```

3. Створіть віртуальне середовище Python

```bash
python -m venv myenv
```

4. Активуйте віртуальне середовище (команди можуть відрізнятися залежно від операційної системи):

* Для Windows
    ```bash
    myenv\Scripts\activate
    ```

* Для macOS and Linux
    ```bash
    source myenv/bin/activate
    ```


5. Встановіть проект BondsTool
```bash
pip install .
```

6. Запустіть програму BondsTool
```bash
python src/bondstool/app.py
```


## Використання

Команда запуску надасть url-адресу, за якою програма буде доступна.

За замовчуванням програма відобразить аналіз файлу-прикладу, створеного вручну. Для обробки ваших даних скористайтеся кнопкою під заголовком, щоб завантажити файл у відповідному форматі.

Використовуйте файл за замовчуванням як приклад необхідного формату. Він знаходиться в [`BondsTool/assets/example_bag.xlsx`](BondsTool/assets/example_bag.xlsx).


## Додати лого (необов'язково)

Для завантаження логотипу компанії на веб-сторінку необхідно зберегти файл із зображенням логотипу у директорію [`BondsTool/assets`](BondsTool/assets) на вашому пристрої з назвою `logo.png`.


 ## Розгортання на сервері (необов'язково)

Аби розгорнути програму на сервері:

* Для Windows
    ```bash
    waitress-serve --listen=*:8050 src.bondstool.app:server
    ```

* Для macOS and Linux
    ```bash
    gunicorn src.bondstool.app:server -b :8050
    ```
