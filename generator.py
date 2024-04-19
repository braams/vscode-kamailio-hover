#!/usr/bin/python
import json
import logging
import os
import re
import shutil
import urllib.request

import mistune
import pypandoc
from lxml import etree
from mistune.renderers.markdown import MarkdownRenderer

src_version = "5.8.1"
cookbook_version = "5.8.x"

src_url = "https://github.com/kamailio/kamailio/archive/refs/tags/%s.zip"
cookbook_url = "https://raw.githubusercontent.com/kamailio/kamailio-wiki/main/docs/cookbooks/%s/%s.md"
tmp_dir = "tmp"

exclude = ['app_python', 'uid_auth_db', 'uid_gflags', 'ims_dialog', 'uid_domain', 'ims_registrar_scscf', 'mangler',
           'rtpproxy', 'uid_uri_db']
log = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def maketempdir():
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        log.info("Temporary directory created: %s", tmp_dir)
    else:
        log.info("Temporary directory found: %s", tmp_dir)
    for dir in ["cookbooks", "modules"]:
        newdir = os.path.join(tmp_dir, dir)
        if not os.path.exists(newdir):
            os.makedirs(newdir)
            log.info("Subdirectory created: %s", newdir)
        else:
            log.info("Subdirectory found: %s", newdir)


def download_src(version):
    srczip = src_url % version
    dstzip = os.path.join(tmp_dir, os.path.basename(srczip))
    if not os.path.exists(dstzip):
        urllib.request.urlretrieve(srczip, dstzip)
        log.info("Source code downloaded: %s %s", srczip, dstzip)
    else:
        log.info("Source code found: %s", dstzip)

    dstdir = os.path.join(tmp_dir, "kamailio-%s" % version)
    if not os.path.exists(dstdir):
        shutil.unpack_archive(dstzip, tmp_dir)
        log.info("Source code unpacked: %s", dstdir)
    else:
        log.info("Source code already unpacked: %s", dstdir)
    return dstdir


def download_cookbook(version, book):
    src = cookbook_url % (version, book)
    dst = os.path.join(tmp_dir, "cookbooks", os.path.basename(src))
    if not os.path.exists(dst):
        urllib.request.urlretrieve(src, dst)
        log.info("Cookbook downloaded: %s %s", src, dst)
    else:
        log.info("Cookbook found: %s", dst)


def list_modules(version):
    moddir = os.path.join(tmp_dir, "kamailio-%s" % version, "src", "modules")
    mods = [name for name in os.listdir(moddir)]
    mods.sort()
    return mods


def convert_doc(version, module):
    docdir = os.path.join(tmp_dir, "kamailio-%s" % version, "src", "modules", module, "doc")
    docfile = os.path.join(docdir, "%s.xml" % module)

    fulldocdir = os.path.join(tmp_dir, "modules")

    mdfile = os.path.join(fulldocdir, "%s.md" % module)
    if not os.path.exists(mdfile):
        parser = etree.XMLParser(load_dtd=True, no_network=False)
        tree = etree.parse(docfile, parser=parser)
        tree.xinclude()
        content = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8")
        output = pypandoc.convert_text(content, 'gfm', format='docbook')
        with open(mdfile, 'w', encoding='utf-8') as f:
            f.write(output)
        log.info("Documentation converted: %s", mdfile)
    else:
        log.info("Documentation already converted: %s", mdfile)


def parse_transformation(name):
    return re.findall(r'\{([a-zA-Z0-9_.]+)', name)[0]


def parse_pseudovariable(name):
    if name == '$':
        return '$_s'
    if name.startswith("$$"):
        return '$$'
    return re.findall(r'\$([a-zA-Z0-9_]+)', name)[0]


def parse_name(name):
    return re.findall(r'([a-zA-Z0-9_]+)', name)[0]


def get_ast(filename):
    f = open(filename, 'r', encoding='utf-8')
    mdparser = mistune.Markdown()
    return mdparser(f.read())


def ast2str(ast):
    state = mistune.BlockState()
    mdrenderer = MarkdownRenderer()
    return mdrenderer(ast, state)


def heading(token):
    return token['children'][0]['raw'], token['attrs']['level']


def is_heading(token):
    return token['type'] == 'heading'


class Path:
    level = 0
    heads = ["", "", "", "", "", "", ""]

    def set(self, head: str, level: int):
        self.heads[level] = head
        self.level = level

    def last(self):
        return self.heads[self.level]

    def prev(self):
        return self.heads[1:self.level]

    def full(self):
        return self.heads[1:self.level + 1]

    def is_overview(self):
        return self.full() == ['Admin Guide', 'Overview']

    def is_parameter(self):
        return self.prev() == ['Admin Guide', 'Parameters']

    def is_function(self):
        return self.prev() == ['Admin Guide', 'Functions']

    def is_core_function(self):
        return self.prev() == ['Core Cookbook', 'Core Functions']

    def is_core_parameter(self):
        return self.prev() in [
            ['Core Cookbook', 'Core parameters'],
            ['Core Cookbook', 'DNS Parameters'],
            ['Core Cookbook', 'TCP Parameters'],
            ['Core Cookbook', 'TLS Parameters'],
            ['Core Cookbook', 'SCTP Parameters'],
            ['Core Cookbook', 'UDP Parameters'],
            ['Core Cookbook', 'Blocklist Parameters'],
            ['Core Cookbook', 'Real-Time Parameters'],
        ]

    def is_core_keyword(self):
        return self.prev() in [
            ['Core Cookbook', 'Routing Blocks'],
            ['Core Cookbook', 'Core Keywords'],
            ['Core Cookbook', 'Core Values'],
        ]

    def is_pseudovariable(self):
        return self.heads[1] == 'Pseudo-Variables' and self.heads[self.level].startswith('$')

    def is_transformation(self):
        return self.heads[1] == 'Transformations' and self.heads[self.level].startswith('{')


def extract_module(mod) -> dict:
    log.info("Extracting Module: %s", mod)
    p = Path()

    mdfile = os.path.join(tmp_dir, "modules", mod + ".md")
    ast = get_ast(mdfile)

    name = ""
    overview = []
    parameters = {}
    functions = {}
    data = {
        'overview': "",
        'parameters': {},
        'functions': {},
    }
    for token in ast:
        if is_heading(token):
            h, l = heading(token)
            p.set(h, l)

            if h == "":
                continue

            if p.is_parameter():
                name = parse_name(h)
                parameters[name] = []
                parameters[name].append(token)

            if p.is_function():
                name = parse_name(h)
                functions[name] = []
                functions[name].append(token)

        else:
            if p.is_overview():
                overview.append(token)

            if p.is_parameter():
                if name:
                    parameters[name].append(token)

            if p.is_function():
                if name:
                    functions[name].append(token)

    data['overview'] = ast2str(overview)

    for k, v in parameters.items():
        data['parameters'][k] = ast2str(v)

    for k, v in functions.items():
        data['functions'][k] = ast2str(v)

    return data


def json_dump(file, data):
    jsonfile = os.path.join(tmp_dir, file)
    with open(jsonfile, "w+") as f:
        json.dump(data, f, indent=1)


def extract_cookbook(book) -> dict:
    log.info("Extracting Book: %s", book)
    p = Path()

    mdfile = os.path.join(tmp_dir, "cookbooks", book + ".md")
    ast = get_ast(mdfile)

    name = ""
    parameters = {}
    functions = {}
    keywords = {}
    pseudovariables = {}
    transformations = {}

    data = {}
    for token in ast:
        if is_heading(token):
            h, l = heading(token)
            p.set(h, l)

            if p.is_core_parameter():
                name = parse_name(h)
                parameters[name] = []
                parameters[name].append(token)

            if p.is_core_function():
                name = parse_name(h)
                functions[name] = []
                functions[name].append(token)

            if p.is_core_keyword():
                name = parse_name(h)
                keywords[name] = []
                keywords[name].append(token)

            if p.is_pseudovariable():
                name = parse_pseudovariable(h)
                pseudovariables[name] = []
                pseudovariables[name].append(token)

            if p.is_transformation():
                name = parse_transformation(h)
                transformations[name] = []

        else:

            if p.is_core_parameter():
                parameters[name].append(token)

            if p.is_core_function():
                functions[name].append(token)

            if p.is_core_keyword():
                keywords[name].append(token)

            if p.is_pseudovariable():
                pseudovariables[name].append(token)

            if p.is_transformation():
                transformations[name].append(token)

    if parameters:
        data['parameters'] = {}
        for k, v in parameters.items():
            data['parameters'][k] = ast2str(v)

    if functions:
        data['functions'] = {}
        for k, v in functions.items():
            data['functions'][k] = ast2str(v)

    if keywords:
        data['keywords'] = {}
        for k, v in keywords.items():
            data['keywords'][k] = ast2str(v)

    if transformations:
        data['transformations'] = {}
        for k, v in transformations.items():
            data['transformations'][k] = ast2str(v)

    if pseudovariables:
        data['pseudovariables'] = {}
        for k, v in pseudovariables.items():
            data['pseudovariables'][k] = ast2str(v)

    return data


if __name__ == '__main__':
    maketempdir()

    download_src(src_version)
    modules = list_modules(src_version)
    log.info("Modules found: %d", len(modules))

    modules = [m for m in modules if m not in exclude]

    for mod in modules:
        convert_doc(src_version, mod)

    data = {}
    for mod in modules:
        data[mod] = extract_module(mod)
    json_dump("modules.json", data)

    cookbooks = ["core", "pseudovariables", "transformations"]
    data = {}
    for book in cookbooks:
        download_cookbook(cookbook_version, book)
        data.update(extract_cookbook(book))

    json_dump("core.json", data)
    log.info("Done")
