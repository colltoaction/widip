%{
/* YAML 1.2 Lexer - Indentation Aware */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include "y.tab.h"

extern YYSTYPE yylval;

/* Indentation stack */
int indent_stack[100] = {0};
int indent_level = 0;

/* Token queue for INDENT/DEDENT */
int token_queue[100];
int q_head = 0, q_tail = 0;

void enqueue(int t) { 
    if (q_tail < 100) token_queue[q_tail++] = t; 
}
int dequeue() { 
    if (q_head < q_tail) return token_queue[q_head++]; 
    return 0;
}
bool q_empty() { return q_head == q_tail; }

int real_yylex();

int yylex() {
    if (!q_empty()) return dequeue();
    return real_yylex();
}

#define yylex real_yylex
%}

%option noyywrap
%option yylineno

%x LINESTART

SPACE       [ ]
TAB         [\t]
NEWLINE     \n|\r\n|\r
WS          [ \t]

DIGIT       [0-9]
ALPHA       [a-zA-Z_]
ALNUM       [a-zA-Z0-9_]
PLAIN_CHAR  [a-zA-Z0-9_\-./!@#$%&()=+~\\:]

%%

<INITIAL>^{SPACE}*      { BEGIN(LINESTART); yyless(0); }

<LINESTART>{SPACE}*/{NEWLINE} {
                          /* Ignore whitespace-only lines */
                          BEGIN(INITIAL);
                        }

<LINESTART>{SPACE}*"#" {
                          /* Ignore indentation for comment lines */
                          BEGIN(INITIAL);
                          yyless(yyleng - 1);
                        }

<LINESTART>{SPACE}*     {
                          BEGIN(INITIAL);
                          int indent = yyleng;
                          if (indent > indent_stack[indent_level]) {
                              indent_stack[++indent_level] = indent;
                              return INDENT;
                          } else if (indent < indent_stack[indent_level]) {
                              while (indent < indent_stack[indent_level]) {
                                  indent_level--;
                                  enqueue(DEDENT);
                              }
                              return dequeue();
                          }
                        }

^%.*                    { /* Ignore directives */ }

"---"                   { return DOC_START; }
"..."                   { return DOC_END; }

"["                     { return LBRACKET; }
"]"                     { return RBRACKET; }
"{"                     { return LBRACE; }
"}"                     { return RBRACE; }
","                     { return COMMA; }

"-"{WS}+                { return SEQ_ENTRY; }
"-"{NEWLINE}            { return SEQ_ENTRY; }
"?"{WS}+                { return MAP_KEY; }
": "{WS}*               { return COLON; }
":"/{NEWLINE}           { return COLON; }
":"/","                 { return COLON; }
":"/"}"                 { return COLON; }

"&"{ALNUM}+             { yylval.str = strdup(yytext+1); return ANCHOR; }
"*"{ALNUM}+             { yylval.str = strdup(yytext+1); return ALIAS; }
"!"{PLAIN_CHAR}*        { yylval.str = strdup(yytext+1); return TAG; }

"#"[^\n\r]*             { /* Comment - ignore */ }

\"([^\"\\]|\\.)*\"      { 
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return DQUOTE_STRING;
                        }

\'[^\']*\'              {
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return SQUOTE_STRING;
                        }

{PLAIN_CHAR}+({WS}+{PLAIN_CHAR}+)*  { yylval.str = strdup(yytext); return PLAIN_SCALAR; }

{NEWLINE}               { return NEWLINE; }
{WS}+                   { /* Ignore other whitespace */ }

.                       { return yytext[0]; }

<<EOF>>                 {
                          while (indent_level > 0) {
                              indent_level--;
                              enqueue(DEDENT);
                          }
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

%%

#undef yylex
