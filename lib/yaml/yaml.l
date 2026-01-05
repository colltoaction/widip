%{
/* YAML Lexer - Refined for LALR(1) compatibility */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include "y.tab.h"

extern YYSTYPE yylval;
int indent_stack[100] = {0}, indent_level = 0, flow_level = 0;
int token_queue[1024], q_head = 0, q_tail = 0;

void enqueue(int t) { if (q_tail < 1024) token_queue[q_tail++] = t; }
int dequeue() { return (q_head < q_tail) ? token_queue[q_head++] : 0; }

int process_indent(int indent) {
    if (flow_level > 0) return 0;
    if (indent > indent_stack[indent_level]) {
        indent_stack[++indent_level] = indent;
        return INDENT;
    }
    while (indent < indent_stack[indent_level] && indent_level > 0) {
        indent_level--; enqueue(DEDENT);
    }
    return dequeue();
}

int real_yylex();
int next_tok = -1;

int yylex() {
    int tok;
    if (next_tok != -1) { tok = next_tok; next_tok = -1; return tok; }
    tok = (q_head < q_tail) ? dequeue() : real_yylex();
    if (tok == NEWLINE) {
        int following = real_yylex();
        if (following == INDENT) return NEWLINE_INDENT;
        if (following == DEDENT) return NEWLINE_DEDENT;
        next_tok = following;
    }
    return tok;
}

const char* tok_name(int tok) {
    switch(tok) {
        case DOC_START: return "DOC_START"; case DOC_END: return "DOC_END";
        case LBRACKET: return "LBRACKET"; case RBRACKET: return "RBRACKET";
        case LBRACE: return "LBRACE"; case RBRACE: return "RBRACE";
        case COMMA: return "COMMA"; case SEQ_ENTRY: return "SEQ_ENTRY";
        case MAP_KEY: return "MAP_KEY"; case COLON: return "COLON";
        case NEWLINE: return "NEWLINE"; case INDENT: return "INDENT";
        case DEDENT: return "DEDENT"; case NEWLINE_DEDENT: return "NEWLINE_DEDENT";
        case NEWLINE_INDENT: return "NEWLINE_INDENT"; case ANCHOR: return "ANCHOR";
        case ALIAS: return "ALIAS"; case TAG: return "TAG";
        case PLAIN_SCALAR: return "PLAIN_SCALAR"; case DQUOTE_STRING: return "DQUOTE_STRING";
        case SQUOTE_STRING: return "SQUOTE_STRING"; case LITERAL: return "LITERAL";
        case FOLDED: return "FOLDED"; case LITERAL_CONTENT: return "LITERAL_CONTENT";
        default: return "CHAR";
    }
}
#define yylex real_yylex
%}

%option noyywrap yylineno
%x BOL FLOW
NEWLINE     \n|\r\n|\r
SEP         [ \t\n\r,\[\]\{\}]
SAFE_S_BLK  [^ \t\n\r\-\?:,\[\]\{\}!#&*|>\x22\x27%@\x60]
SAFE_C_BLK  [^ \t\n\r,\[\]\{\}:!]

%%

<BOL>[ \t]* { 
    int indent = 0;
    for (int i = 0; i < yyleng; i++) indent += (yytext[i] == '\t') ? 8 - (indent % 8) : 1;
    BEGIN(INITIAL);
    int tok = process_indent(indent);
    if (tok) return tok;
}
<BOL>{NEWLINE} { return NEWLINE; }
<BOL><<EOF>>   { while (indent_level >= 0) { indent_level--; enqueue(DEDENT); } return dequeue(); }
<BOL>.         { yyless(0); BEGIN(INITIAL); }

<INITIAL,FLOW>"---"/({SEP}|$) { return DOC_START; }
<INITIAL,FLOW>"..."/({SEP}|$) { return DOC_END; }
<INITIAL>"-"/({SEP}|$)        { return SEQ_ENTRY; }
<INITIAL>":"/({SEP}|$)        { return COLON; }
<INITIAL,FLOW>","                          { return COMMA; }
<INITIAL,FLOW>"["                          { flow_level++; BEGIN(FLOW); return LBRACKET; }
<FLOW>"]"                                  { if (--flow_level == 0) BEGIN(INITIAL); return RBRACKET; }
<INITIAL,FLOW>"{"                          { flow_level++; BEGIN(FLOW); return LBRACE; }
<FLOW>"}"                                  { if (--flow_level == 0) BEGIN(INITIAL); return RBRACE; }
<FLOW>":"                                  { return COLON; }

<INITIAL,FLOW>"&"[a-zA-Z0-9_\-]+           { yylval.str = strdup(yytext+1); return ANCHOR; }
<INITIAL,FLOW>"*"[a-zA-Z0-9_\-]+           { yylval.str = strdup(yytext+1); return ALIAS; }
<INITIAL,FLOW>"!"[a-zA-Z0-9_\-./!@#$%&()=+~\\<>]* { yylval.str = strdup(yytext+1); return TAG; }

<INITIAL,FLOW>\"([^\"\\]|\\.)*\"           { yylval.str = strndup(yytext+1, yyleng-2); return DQUOTE_STRING; }
<INITIAL,FLOW>\'[^\']*\'                   { yylval.str = strndup(yytext+1, yyleng-2); return SQUOTE_STRING; }

<INITIAL,FLOW>{SAFE_S_BLK}({SAFE_C_BLK}|":"[^ \t\n\r,\[\]\{\}])*[!#&*|%>]* { yylval.str = strdup(yytext); return PLAIN_SCALAR; }
<INITIAL,FLOW>[\-\?:][^ \t\n\r,\[\]\{\}]+ { yylval.str = strdup(yytext); return PLAIN_SCALAR; }

<INITIAL,FLOW>"#"[^\n\r]*                  { /* ignore */ }
<INITIAL>{NEWLINE}                         { BEGIN(BOL); return NEWLINE; }
<FLOW>{NEWLINE}                            { /* ignore */ }
[ \t]+                                     { /* whitespace */ }
.                                          { return yytext[0]; }
<<EOF>>                                    { while (indent_level >= 0) { indent_level--; enqueue(DEDENT); } if (q_head < q_tail) return dequeue(); return 0; }

%%
#undef yylex
