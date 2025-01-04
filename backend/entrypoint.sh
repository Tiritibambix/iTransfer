#!/bin/bash

# Exécuter les migrations
flask db upgrade

# Lancer l'application
exec "$@"
