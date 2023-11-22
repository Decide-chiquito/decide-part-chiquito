#!/bin/bash
# *********************************************************************************************************************
# Script para ejecutar comandos Django en macOS y Linux
# El script asume que se encuentra en la raíz del proyecto
# Para ejecutar, primero da permisos de ejecución con 'chmod +x init.sh'
# Luego, ejecute con './init.sh'
# *********************************************************************************************************************

nocheck=0
novenv=0
nodependencies=0
persist=0
notest=0

while [ "$1" != "" ]; do
    case $1 in
        --help)
            echo "Usage: ./init.sh [--nocheck] [--novenv] [--nodependencies] [--persist] [--notest] [--help]"
            echo "Options:"
            echo "  --help    Show this help message."
            echo "  --nocheck  Skip the Python version check."
            echo "  --novenv  Skip the virtual environment creation."
            echo "  --nodependencies  Skip the dependencies installation."
            echo "  --persist  Persist the database."
            echo "  --notest  Skip the test execution."
            exit 0
            ;;
        --nocheck)
            nocheck=1
            ;;
        --novenv)
            novenv=1
            ;;
        --nodependencies)
            nodependencies=1
            ;;
        --persist)
            persist=1
            ;;
        --notest)
            notest=1
            ;;
    esac
    shift
done

echo "####################################################################"
echo "#                                                                  #"
echo "#                                                                  #"
echo "#      ██████████                      ███      █████              #"
echo "#     ░░███░░░░███                    ░░░      ░░███               #"
echo "#      ░███   ░░███  ██████   ██████  ████   ███████   ██████      #"
echo "#      ░███    ░███ ███░░███ ███░░███░░███  ███░░███  ███░░███     #"
echo "#      ░███    ░███░███████ ░███ ░░░  ░███ ░███ ░███ ░███████      #"
echo "#      ░███    ███ ░███░░░  ░███  ███ ░███ ░███ ░███ ░███░░░       #"
echo "#      ██████████  ░░██████ ░░██████  █████░░████████░░██████      #"
echo "#     ░░░░░░░░░░    ░░░░░░   ░░░░░░  ░░░░░  ░░░░░░░░  ░░░░░░       #"
echo "#                                                                  #"
echo "#                                                                  #"
echo "####################################################################"
echo ""
echo ""

if [ $nocheck -eq 1 ]; then
    echo "========== SKIPPING PYTHON VERSION CHECK =========="
    echo "Skipping Python version check because of --nocheck argument."
    echo ""
else
    echo "========== CHECKING PYTHON VERSION =========="
    echo "Checking Python version..."
    python3 -c "import sys; assert sys.version_info[:2] == (3, 10), 'Incorrect Python version, requires Python 3.10'; print('Correct Python version (3.10)')"
    if [ $? -ne 0 ]; then
        echo "Python version is not 3.10. Exiting..."
        exit 1
    fi
    echo ""
fi

if [ $novenv -eq 1 ]; then
    echo "========== SKIPPING VENV =========="
    echo "Skipping virtual environment creation because of --novenv argument."
    echo ""
else
    echo "========== DELETING VIRTUAL ENVIRONMENT =========="
    echo "Deleting virtual environment..."
    rm -rf venv
    echo ""

    echo "========== CREATING VIRTUAL ENVIRONMENT =========="
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

echo "========== ACTIVATING VIRTUAL ENVIRONMENT =========="
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

echo "========== SETTING GIT COMMIT TEMPLATE =========="
echo "Setting Git commit template..."
git config commit.template .gitmessage.txt
echo ""

echo "========== UPDATING PIP =========="
echo "Updating pip..."
python -m pip install --upgrade pip
echo ""

if [ $nodependencies -eq 1 ]; then
    echo "========== SKIPPING DEPENDENCIES INSTALLATION =========="
    echo "Skipping dependencies installation because of --nodependencies argument."
    echo ""
else
    echo "========== INSTALLING DEPENDENCIES =========="
    echo "Installing dependencies from requirements.txt..."
    pip install -r ./requirements.txt
    echo ""
fi

cd decide

if [ $persist -eq 1 ]; then
    echo "========== PERSISTING DATABASE =========="
    echo "Persisting database because of --persist argument."
    echo ""
else
    echo "========== DROPPING DATABASE =========="
    echo "Dropping database..."
    ./manage.py reset_db --noinput
    echo ""

    echo "========== CLEARING CACHE =========="
    echo "Clearing cache..."
    find . -name '__pycache__' -print -exec rm -rf {} +
    echo ""

    echo "========== DELETING MIGRATIONS =========="
    echo "Deleting migrations and recreating directories..."
    for d in */; do
        if [ -d "${d}migrations" ] && [ "${d}" != "venv/" ]; then
            echo "Deleting migrations directory: ${d}migrations"
            rm -rf "${d}migrations"
        fi
        echo "Creating migrations directory: ${d}migrations"
        mkdir -p "${d}migrations"
        echo "Creating file: ${d}migrations/__init__.py"
        touch "${d}migrations/__init__.py"
    done
    echo ""
fi

echo "========== MAKEMIGRATIONS =========="
echo "Running makemigrations..."
./manage.py makemigrations
echo ""

echo "========== MIGRATE =========="
echo "Running migrate..."
./manage.py migrate
echo ""

if [ $notest -eq 1 ]; then
    echo "========== SKIPPING TESTS =========="
    echo "Skipping test execution because of --notest argument."
    echo ""
else
    echo "========== TEST =========="
    echo "Running tests..."
    ./manage.py test
    echo ""

    echo "========== COVERAGE REPORT =========="
    echo "Generating coverage report..."
    coverage run --source='.' manage.py test
    coverage report
    coverage html
    echo ""
fi

echo "========== LOAD DATA =========="
echo "Loading data from populate.json..."
./manage.py loaddata populate.json
echo ""

echo "========== RUN SERVER =========="
echo "Starting the server..."
./manage.py runserver
echo ""
