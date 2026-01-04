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
int flow_level = 0;      /* Nesting level of flow style [] and {} */

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
    if (flow_level > 0) return 0;
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

int block_start_indent = -1;
char *block_buffer = NULL;
int block_buf_size = 0;
int block_buf_len = 0;

void append_block(const char *s) {
    int len = strlen(s);
    if (block_buf_len + len + 2 > block_buf_size) {
        block_buf_size = (block_buf_len + len + 2) * 2;
        if (block_buf_size < 1024) block_buf_size = 1024;
        block_buffer = realloc(block_buffer, block_buf_size);
    }
    strcpy(block_buffer + block_buf_len, s);
    block_buf_len += len;
}

int real_yylex();

int yylex() {
    int tok;
    if (!q_empty()) {
        tok = dequeue();
        return tok;
    }
    tok = real_yylex();
    return tok;
}

#define yylex real_yylex
%}

%option noyywrap
%option yylineno
%option stack

/* Start conditions */
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
        yy_push_state(BOL);
    }
%}

<BOL>[ ]+               { 
                          pending_indent = yyleng;
                        }

<BOL>{NEWLINE}          { 
                          pending_indent = 0;
                          return NEWLINE; 
                        }

<BOL><<EOF>>            {
                          while (indent_level > 0) {
                              indent_level--;
                              enqueue(DEDENT);
                          }
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

<BOL>.                  { 
                          yyless(0);
                          BEGIN(INITIAL);
                          int tok = process_indent(pending_indent);
                          pending_indent = 0;
                          if (tok) return tok;
                        }

<INITIAL>^%.*           { /* Ignore directives */ }
<INITIAL>"---"          { return DOC_START; }
<INITIAL>"..."          { return DOC_END; }

<INITIAL>("|"|">")([+-]|[0-9]|[+-][0-9]|[0-9][+-])?([ ]*|([ ]*"#"[^\n\r]*)){NEWLINE} { 
                          int base_indent = indent_stack[indent_level];
                          int folded = (yytext[0] == '>');
                          int tok = folded ? FOLDED : LITERAL;
                          
                          block_buf_len = 0;
                          if (block_buffer) block_buffer[0] = '\0';
                          
                          int c;
                          while (1) {
                              int indent = 0;
                              int pos = 0;
                              char line_buf[1024];
                              
                              // Read leading whitespace
                              while ((c = input()) == ' ' || c == '\t') {
                                  if (c == ' ') indent++;
                                  else indent = (indent + 8) & ~7;
                                  if (pos < 1023) line_buf[pos++] = c;
                              }
                              
                              if (c == EOF) break;
                              
                              // Check for empty line
                              if (c == '\n' || c == '\r') {
                                  if (c == '\r') {
                                      int c2 = input();
                                      if (c2 != '\n' && c2 != EOF) unput(c2);
                                  }
                                  append_block("\n");
                                  continue;
                              }
                              
                              // Check for de-indentation
                              if (indent <= base_indent) {
                                  // Return things to stream
                                  unput(c);
                                  for (int i = pos - 1; i >= 0; i--) unput(line_buf[i]);
                                  break;
                              }
                              
                              // Read the rest of the line
                              line_buf[pos++] = c;
                              while ((c = input()) != '\n' && c != '\r' && c != EOF) {
                                  if (pos < 1023) line_buf[pos++] = c;
                              }
                              line_buf[pos] = '\0';
                              
                              // Append content (stripping base indent)
                              int skip = (indent > base_indent) ? base_indent : indent;
                              append_block(line_buf + skip);
                              append_block("\n");
                              
                              if (c == EOF) break;
                              if (c == '\r') {
                                  int c2 = input();
                                  if (c2 != '\n' && c2 != EOF) unput(c2);
                              }
                          }
                          
                          yylval.str = strdup(block_buffer ? block_buffer : "");
                          enqueue(LITERAL_CONTENT);
                          return tok;
                        }

<INITIAL>"["            { flow_level++; return LBRACKET; }
<INITIAL>"]"            { if (flow_level > 0) flow_level--; return RBRACKET; }
<INITIAL>"{"            { flow_level++; return LBRACE; }
<INITIAL>"}"            { if (flow_level > 0) flow_level--; return RBRACE; }
<INITIAL>","            { return COMMA; }

<INITIAL>"-"            { return SEQ_ENTRY; }
<INITIAL>"?"            { return MAP_KEY; }
<INITIAL>":"            { return COLON; }

<INITIAL>"&"{ALNUM}+    { yylval.str = strdup(yytext+1); return ANCHOR; }
<INITIAL>"*"{ALNUM}+    { yylval.str = strdup(yytext+1); return ALIAS; }
<INITIAL>"!"{PLAIN_CONT}* { yylval.str = strdup(yytext+1); return TAG; }

<INITIAL>"#"[^\n\r]*    { /* Comment */ }

<INITIAL>\"([^\"\\]|\\.)*\" { 
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return DQUOTE_STRING;
                        }

<INITIAL>\'[^\']*\'     {
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return SQUOTE_STRING;
                        }

<INITIAL>[a-zA-Z0-9_./@#$%&()=+~\\][a-zA-Z0-9_\-./!@#$%&()=+~\\]*([ \t]+[a-zA-Z0-9_\-./!@#$%&()=+~\\]+)* { 
                          yylval.str = strdup(yytext); return PLAIN_SCALAR; 
                        }

<INITIAL>{NEWLINE}      { 
                          pending_indent = 0;
                          BEGIN(BOL); 
                          if (flow_level == 0) return NEWLINE; 
                        }

<INITIAL>[ \t]+         { /* Whitespace */ }

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
