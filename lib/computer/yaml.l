%{
/* YAML 1.2 Lexer - Simplified Subset */
#include <stdio.h>
#include <string.h>
#include "y.tab.h"

int current_indent = 0;
int pending_indent = 0;

extern YYSTYPE yylval;
%}

%option noyywrap
%option yylineno

SPACE       [ ]
TAB         [\t]
NEWLINE     \n|\r\n|\r
WS          [ \t]

DIGIT       [0-9]
ALPHA       [a-zA-Z_]
ALNUM       [a-zA-Z0-9_]
PLAIN_CHAR  [a-zA-Z0-9_\-./]

%%

"---"                   { return DOC_START; }
"..."                   { return DOC_END; }

"["                     { return LBRACKET; }
"]"                     { return RBRACKET; }
"{"                     { return LBRACE; }
"}"                     { return RBRACE; }
","                     { return COMMA; }

"-"{WS}                 { return SEQ_ENTRY; }
"?"{WS}                 { return MAP_KEY; }
":"{WS}                 { return COLON; }
":"/{NEWLINE}           { return COLON; }
":"$                    { return COLON; }

"&"{ALNUM}+             { yylval.str = strdup(yytext+1); return ANCHOR; }
"*"{ALNUM}+             { yylval.str = strdup(yytext+1); return ALIAS; }
"!"{PLAIN_CHAR}*        { yylval.str = strdup(yytext+1); return TAG; }

"#"[^\n\r]*             { /* Comment - ignore */ }

\"([^\"\\]|\\.)*\"      { 
                          /* Double-quoted string */
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return DQUOTE_STRING;
                        }

\'([^\'\\]|\\.)*\'      {
                          /* Single-quoted string */
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return SQUOTE_STRING;
                        }

{PLAIN_CHAR}+           { yylval.str = strdup(yytext); return PLAIN_SCALAR; }

^{SPACE}+               { 
                          pending_indent = yyleng;
                          /* Indentation - track for block structure */
                        }

{NEWLINE}               { current_indent = 0; return NEWLINE; }
{WS}+                   { /* Ignore other whitespace */ }

.                       { return yytext[0]; }

%%
