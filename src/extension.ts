import * as vscode from 'vscode';

import core from './generated/core.json';
import modules from './generated/modules.json';

export function activate(context: vscode.ExtensionContext) {
	vscode.languages.registerHoverProvider('kamailio', {
		provideHover(document, position, token) {

			const transRe = /\{[a-zA-Z\.]+/;
			const pseudoRe = /\$[a-zA-Z]\w+/;
			const coreRe = /[a-z][a-z_]+/;
			const funcsRe = /[a-z][a-z0-9_]+/;

			var hover = lookupLoadModule(document, position, modules);
			if (hover) {
				return hover;
			}

			var hover = lookupModParam(document, position, modules);
			if (hover) {
				return hover;
			}

			var hover = lookupTrans(document, position, transRe, core);
			if (hover) {
				return hover;
			}
			hover = lookupPseudo(document, position, pseudoRe, core);
			if (hover) {
				return hover;
			}
			hover = lookupCore(document, position, coreRe, core);
			if (hover) {
				return hover;
			}
			hover = lookupFunctions(document, position, funcsRe, modules);
			if (hover) {
				return hover;
			}

			return null;
		}
	});
}

export function deactivate() { }

function lookupPseudo(document: vscode.TextDocument, position: vscode.Position, re: RegExp, data: any) {
	const range = document.getWordRangeAtPosition(position, re);
	if (!range) {
		return null;
	}
	const word = document.getText(range).substring(1);

	if (data['pseudovariables'] && data['pseudovariables'][word]) {
		const val = data['pseudovariables'][word];
		const content = new vscode.MarkdownString(val);

		return {
			contents: [content]
		};
	}
	return null;
}

function lookupTrans(document: vscode.TextDocument, position: vscode.Position, re: RegExp, data: any) {
	const range = document.getWordRangeAtPosition(position, re);
	if (!range) {
		return null;
	}
	const word = document.getText(range).substring(1);

	if (data['transformations'] && data['transformations'][word]) {
		const val = data['transformations'][word];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}
	return null;
}


function lookupFunctions(document: vscode.TextDocument, position: vscode.Position, re: RegExp, data: any) {
	const range = document.getWordRangeAtPosition(position, re);
	if (!range) {
		return null;
	}
	const word = document.getText(range);

	var val;
	Object.keys(data).forEach((mod) => {
		if (data[mod] && data[mod]['functions'] && data[mod]['functions'][word]) {
			val = data[mod]['functions'][word];
		}
	});
	if (val) {
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}
	return null;

}

function lookupCore(document: vscode.TextDocument, position: vscode.Position, re: RegExp, data: any) {
	const range = document.getWordRangeAtPosition(position, re);
	if (!range) {
		return null;
	}
	const word = document.getText(range);

	if (data['parameters'][word]) {
		const val = data['parameters'][word];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}
	if (data['functions'][word]) {
		const val = data['functions'][word];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}
	if (data['keywords'][word]) {
		const val = data['keywords'][word];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}
	return null;
}

function lookupLoadModule(document: vscode.TextDocument, position: vscode.Position, data: any) {
	const line = document.lineAt(position);
	if (!line.text.includes('loadmodule')) {
		return null;
	}
	const range = document.getWordRangeAtPosition(position);
	if (!range) {
		return null;
	}
	const word = document.getText(range);
	if (data[word] && data[word]['overview']) {
		const val = "### " + word + "\n\n" + data[word]['overview'];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}

	return null;
}


function lookupModParam(document: vscode.TextDocument, position: vscode.Position, data: any) {
	const line = document.lineAt(position);
	if (!line.text.includes('modparam(')) {
		return null;
	}

	var mod, param;
	const re = /modparam\('(?<mod>\w+)'[,\s]+'(?<param>\w+)'.*/;
	const match = re.exec(line.text);
	if (match && match.groups) {
		mod = match.groups['mod'];
		param = match.groups['param'];
	} else {
		return null;
	}

	const range = document.getWordRangeAtPosition(position);
	if (!range) {
		return null;
	}
	const word = document.getText(range);
	if (word === mod && data[mod] && data[mod]['overview']) {
		const val = "### " + word + "\n\n" + data[mod]['overview'];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}

	if (word === param && data[mod] && data[mod]['parameters'][param]) {
		const val = data[mod]['parameters'][param];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}

	return null;
}
