# kamailio-hover

This is the Visual Studio Code extension that enhances clarity of the Kamailio configuration.

![Demo](https://raw.githubusercontent.com/braams/vscode-kamailio-hover/master/demo.gif)

## Features

This extension provides documentation for Kamailio configuration file items:
* Global parameters 
* Core keywords
* Core functions
* Module parameters
* Module functions
* Pseudovariables
* Transformations

## Installation

The extension is available on VSCode Marketplace: https://marketplace.visualstudio.com/items?itemName=braamsdev.kamailio-hover

## Tooltips generation
The content for this extension was generated from the documentation of the Kamailio project: https://github.com/kamailio/kamailio/ and https://github.com/kamailio/kamailio-wiki and stored as .json files in the project.

    python3 -m venv .venv                     
    source .venv/bin/activate
    pip install -r requirements.txt
    python3 generator.py
    cp tmp/*.json src/generated

## Useful thing

I also recommend using the extension for syntax highlighting: https://github.com/miconda/vscode-kamailio-syntax
