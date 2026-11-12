# polyglot-code-runner-backend

## Pre-requisities:

Python 3.11

## Step 1:

clone this repository and change directory

git clone git@github.com:shivam-2002/polyglot-code-runner-backend.git

cd polyglot-code-runner-backend

## Step 2:

Create Virtual Environment

```
python3 -m venv venv
```

or

python[your_python_version] -m venv venv

## Step 3:

Activate Virtual Environment

### For Window

```
venv\Scripts\activate
```

### For Linus and Mac

```
source venv/bin/activate
```

## Step 4:

Install dependencies

```
pip install -r requirements.txt
```

## Step 5:

Run the project

```
uvicorn main:app --port [PORT_NUMBER]
```

Replace [PORT_NUMBER] with the port number you want the server to run on, for example 8000.
Replace [your_python_version] with the install python version, it should be latest.
