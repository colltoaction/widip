%{
/* YAML Lexer - LALR friendly with Proactive Synthesized Tokens */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include "y.tab.h"

extern YYSTYPE yylval;

int indent_stack[100] = {0};
int indent_level = 0;
int pending_indent = 0;
int flow_level = 0;

int token_queue[2048];
int q_head = 0, q_tail = 0;

void enqueue(int t) { if (q_tail < 2048) token_queue[q_tail++] = t; }
int dequeue() { if (q_head < q_tail) return token_queue[q_head++]; return 0; }
bool q_empty() { return q_head == q_tail; }
int q_peek() { if (q_head < q_tail) return token_queue[q_head]; return 0; }

int process_indent(int indent) {
    if (flow_level > 0) return 0;
    if (indent > indent_stack[indent_level]) {
        indent_stack[++indent_level] = indent;
        return INDENT;
    } else if (indent < indent_stack[indent_level]) {
        while (indent < indent_stack[indent_level] && indent_level > 0) {
            indent_level--;
            enqueue(DEDENT);
        }
        return dequeue();
    }
    return 0;
}

int real_yylex();

const char* tok_name(int tok) {
    if (tok < 256) {
        static char buf[4] = {0};
        if (tok == '\n') return "NEWLINE_CHAR";
        buf[0] = (char)tok; buf[1] = 0;
        return buf;
    }
    switch(tok) {
        case DOC_START: return "DOC_START";
        case DOC_END: return "DOC_END";
        case LBRACKET: return "LBRACKET";
        case RBRACKET: return "RBRACKET";
        case LBRACE: return "LBRACE";
        case RBRACE: return "RBRACE";
        case COMMA: return "COMMA";
        case SEQ_ENTRY: return "SEQ_ENTRY";
        case MAP_KEY: return "MAP_KEY";
        case COLON: return "COLON";
        case NEWLINE: return "NEWLINE";
        case INDENT: return "INDENT";
        case DEDENT: return "DEDENT";
        case NEWLINE_DEDENT: return "NEWLINE_DEDENT";
        case NEWLINE_INDENT: return "NEWLINE_INDENT";
        case ANCHOR: return "ANCHOR";
        case ALIAS: return "ALIAS";
        case TAG: return "TAG";
        case PLAIN_SCALAR: return "PLAIN_SCALAR";
        case DQUOTE_STRING: return "DQUOTE_STRING";
        case SQUOTE_STRING: return "SQUOTE_STRING";
        case LITERAL: return "LITERAL";
        case FOLDED: return "FOLDED";
        case LITERAL_CONTENT: return "LITERAL_CONTENT";
        default: return "OTHER";
    }
}

int yylex() {
    static int next_tok = 0;
    int tok;
    
    if (next_tok) { tok = next_tok; next_tok = 0; return tok; }
    
    if (!q_empty()) tok = dequeue();
    else tok = real_yylex();
    
    if (tok == NEWLINE) {
        /* Proactively call real_yylex to see if an INDENT/DEDENT follows from BOL */
        int following = real_yylex();
        if (following == INDENT) return NEWLINE_INDENT;
        if (following == DEDENT) return NEWLINE_DEDENT;
        next_tok = following;
        return NEWLINE;
    }
    
    return tok;
}

#define yylex real_yylex
%}

%option noyywrap
%option yylineno
%option stack

%x BOL
%x FLOW

NEWLINE     \n|\r\n|\r
SEP         [ \t\n\r,\[\]\{\}]
SAFE_S_BLK  [^ \t\n\r\-\?:,\[\]\{\}!#&*|>\x22\x27%@\x60]
SAFE_C_BLK  [^ \t\n\r,\[\]\{\}:!]

%%

%{
    static int init_begun = 0;
    if (!init_begun) { init_begun = 1; BEGIN(BOL); }
%}

<BOL>[ \t]*             { 
                          int indent = 0;
                          for (int i = 0; i < yyleng; i++) {
                              if (yytext[i] == ' ') indent++;
                              else if (yytext[i] == '\t') indent = (indent + 8) & ~7;
                          }
                          pending_indent = indent;
                        }
<BOL>{NEWLINE}          { pending_indent = 0; return NEWLINE; }
<BOL>.                  { 
                          yyless(0); 
                          BEGIN(INITIAL);
                          int tok = process_indent(pending_indent);
                          pending_indent = 0;
                          if (tok) return tok;
                        }
<BOL><<EOF>>            {
                          while (indent_level >= 0) { indent_level--; enqueue(DEDENT); }
                          return dequeue();
                        }

<INITIAL,FLOW>"---"/({SEP}|$) { return DOC_START; }
<INITIAL,FLOW>"..."/({SEP}|$) { return DOC_END; }

<INITIAL>"-"/({SEP}|$)        { return SEQ_ENTRY; }
<INITIAL>":"/({SEP}|$)        { return COLON; }
<INITIAL>"?"/({SEP}|$)        { return MAP_KEY; }

<INITIAL,FLOW>","             { return COMMA; }
<INITIAL,FLOW>"["             { flow_level++; yy_push_state(FLOW); return LBRACKET; }
<FLOW>"]"                     { if (flow_level > 0) flow_level--; yy_pop_state(); return RBRACKET; }
<INITIAL,FLOW>"{"                 { flow_level++; yy_push_state(FLOW); return LBRACE; }
<FLOW>"}"                         { if (flow_level > 0) flow_level--; yy_pop_state(); return RBRACE; }

<FLOW>":"                         { return COLON; }
<FLOW>"?"                         { return MAP_KEY; }
<FLOW>"-"                         { yylval.str = strdup("-"); return PLAIN_SCALAR; }

<INITIAL,FLOW>"&"[a-zA-Z0-9_\-]+    { yylval.str = strdup(yytext+1); return ANCHOR; }
<INITIAL,FLOW>"*"[a-zA-Z0-9_\-]+    { yylval.str = strdup(yytext+1); return ALIAS; }

<INITIAL,FLOW>"!"[a-zA-Z0-9_\-./!@#$%&()=+~\\<>]* { 
    yylval.str = strdup(yytext+1); 
    return TAG; 
}

<INITIAL,FLOW>\"([^\"\\]|\\.)*\" { 
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return DQUOTE_STRING;
                        }
<INITIAL,FLOW>\'[^\']*\'     {
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return SQUOTE_STRING;
                        }

<INITIAL,FLOW>{SAFE_S_BLK}({SAFE_C_BLK}|":"[^ \t\n\r,\[\]\{\}]|[!#&*|%>])* {
    yylval.str = strdup(yytext);
    return PLAIN_SCALAR;
}

<INITIAL,FLOW>"#"[^\n\r]*    { /* ignore */ }

<INITIAL>{NEWLINE}      { 
                          if (flow_level == 0) {
                              /* Transition to BOL to check for indentation on next call or current lookahead */
                              BEGIN(BOL);
                          }
                          return NEWLINE; 
                        }

<FLOW>{NEWLINE}         { /* ignore */ }
[ \t]+                  { /* whitespace */ }
.                       { return yytext[0]; }

<<EOF>>                 {
                          while (indent_level >= 0) { indent_level--; enqueue(DEDENT); }
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

%%
#undef yylex
