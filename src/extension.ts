import * as vscode from 'vscode';

import core from './generated/core.json';
import pseudovariables from './generated/pseudovariables.json';
import transformations from './generated/transformations.json';
import functions from './generated/functions.json';
import parameters from './generated/parameters.json';

export function activate(context: vscode.ExtensionContext) {
	vscode.languages.registerHoverProvider('kamailio', {
		provideHover(document, position, token) {
			
			const transRe=/\{[a-zA-Z\.]+/;
			const pseudoRe=/\$[a-zA-Z]\w+/;
			const coreRe=/[a-z][a-z_]+/;
			const funcsRe=/[a-z][a-z0-9_]+/;
	
			var hover=lookupModParam(document,position,parameters);
			if (hover){
				return hover;
			}
			var hover=lookup(document,position,transRe,transformations);
			if (hover){
				return hover;
			}
			hover=lookup(document,position,pseudoRe,pseudovariables);
			if (hover){
				return hover;
			}
			hover=lookup(document,position,coreRe,core);
			if (hover){
				return hover;
			}
			hover=lookup(document,position,funcsRe,functions);
			if (hover){
				return hover;
			}
		}
	});
}

export function deactivate() { }

function lookup(document:vscode.TextDocument,position: vscode.Position,re: RegExp, data:any) {
	const range = document.getWordRangeAtPosition(position, re);
	if (!range){
		return null;
	}
	const word = document.getText(range);

	if (data[word]) {
		const val = data[word];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}
	return null;
}

function lookupModParam(document:vscode.TextDocument,position: vscode.Position, data:any) {
	const line=document.lineAt(position);
	if (!line.text.includes("modparam(")){
		return null;
	}

	var mod, param;
	const re=/modparam\("(?<mod>\w+)"[,\s]+"(?<param>\w+)".*/;
	const match = re.exec(line.text);
	if (match && match.groups) {
		mod = match.groups["mod"];
		param = match.groups["param"];
	} else {
		return null;
	}
	
	const range = document.getWordRangeAtPosition(position);
	if (!range){
		return null;
	}
	const word = document.getText(range);
	if (word!=param){
		return null;
	}

	if (data[mod] && data[mod][param])  {
		const val = data[mod][param];
		const content = new vscode.MarkdownString(val);
		return {
			contents: [content]
		};
	}
	return null;
}
