%{
/* YAML 1.2 Lexer - Indentation Aware using Start Conditions */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include "y.tab.h"

extern YYSTYPE yylval;

/* Indentation stack */
int indent_stack[100] = {0};
int indent_level = 0;
int pending_indent = 0;  /* Spaces counted at BOL */

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

/* Process indentation and enqueue tokens */
int process_indent(int indent) {
    if (indent > indent_stack[indent_level]) {
        indent_stack[++indent_level] = indent;
        return INDENT;
    } else if (indent < indent_stack[indent_level]) {
        while (indent < indent_stack[indent_level]) {
            indent_level--;
            if (indent <= indent_stack[indent_level]) {
                if (indent_level > 0 || indent < indent_stack[indent_level]) {
                    enqueue(DEDENT);
                }
            }
        }
        return DEDENT;
    }
    return 0; /* Same level, no token */
}

int real_yylex();

int yylex() {
    if (!q_empty()) return dequeue();
    return real_yylex();
}

#define yylex real_yylex
%}

%option noyywrap
%option yylineno

/* Start conditions - BOL = Beginning Of Line */
%x BOL

WS          [ \t]
NEWLINE     \n|\r\n|\r

DIGIT       [0-9]
ALPHA       [a-zA-Z_]
ALNUM       [a-zA-Z0-9_]
PLAIN_CONT  [a-zA-Z0-9_\-./!@#$%&()=+~\\]

%%

 /* Start in BOL state */
%{
    static int first_call = 1;
    if (first_call) {
        first_call = 0;
        BEGIN(BOL);
    }
%}

<BOL>[ ]+               { 
                          pending_indent = yyleng;
                          /* Don't return anything yet, wait for content */
                        }

<BOL>{NEWLINE}          { 
                          /* Empty line - just reset indent count */
                          pending_indent = 0;
                          return NEWLINE; 
                        }

<BOL><<EOF>>            {
                          /* End of input while at BOL */
                          BEGIN(INITIAL);
                          while (indent_level > 0) {
                              indent_level--;
                              enqueue(DEDENT);
                          }
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

<BOL>.                  { 
                          /* First non-space char on line - process indentation */
                          yyless(0); /* Put the character back */
                          BEGIN(INITIAL);
                          int tok = process_indent(pending_indent);
                          pending_indent = 0;
                          if (tok) return tok;
                        }

<INITIAL>^%.*           { /* Ignore directives at start of line */ }

<INITIAL>"---"          { return DOC_START; }
<INITIAL>"..."          { return DOC_END; }

<INITIAL>"["            { return LBRACKET; }
<INITIAL>"]"            { return RBRACKET; }
<INITIAL>"{"            { return LBRACE; }
<INITIAL>"}"            { return RBRACE; }
<INITIAL>","            { return COMMA; }

<INITIAL>"-"[ \t]+      { return SEQ_ENTRY; }
<INITIAL>"-"/{NEWLINE}  { return SEQ_ENTRY; }
<INITIAL>"?"[ \t]+      { return MAP_KEY; }
<INITIAL>":"[ \t]*      { return COLON; }
<INITIAL>":"/[,}\n\r]   { return COLON; }

<INITIAL>"&"{ALNUM}+    { yylval.str = strdup(yytext+1); return ANCHOR; }
<INITIAL>"*"{ALNUM}+    { yylval.str = strdup(yytext+1); return ALIAS; }
<INITIAL>"!"{PLAIN_CONT}* { yylval.str = strdup(yytext+1); return TAG; }

<INITIAL>"#"[^\n\r]*    { /* Comment - ignore */ }

<INITIAL>\"([^\"\\]|\\.)*\" { 
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return DQUOTE_STRING;
                        }

<INITIAL>\'[^\']*\'     {
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return SQUOTE_STRING;
                        }

<INITIAL>"-"[a-zA-Z0-9_\-./!@#$%&()=+~\\]+([ \t]+[a-zA-Z0-9_\-./!@#$%&()=+~\\]+)* { 
                          yylval.str = strdup(yytext); return PLAIN_SCALAR; 
                        }

<INITIAL>[a-zA-Z0-9_./@#$%&()=+~\\][a-zA-Z0-9_\-./!@#$%&()=+~\\]*([ \t]+[a-zA-Z0-9_\-./!@#$%&()=+~\\]+)* { 
                          yylval.str = strdup(yytext); return PLAIN_SCALAR; 
                        }

<INITIAL>{NEWLINE}      { 
                          pending_indent = 0;
                          BEGIN(BOL); 
                          return NEWLINE; 
                        }

<INITIAL>[ \t]+         { /* Ignore whitespace in middle of line */ }

<INITIAL>.              { return yytext[0]; }

<INITIAL><<EOF>>        {
                          while (indent_level > 0) {
                              indent_level--;
                              enqueue(DEDENT);
                          }
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

%%

#undef yylex
