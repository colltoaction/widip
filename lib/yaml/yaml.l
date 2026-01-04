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
int q_peek() { 
    if (q_head < q_tail) return token_queue[q_head]; 
    return 0;
}

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

const char* tok_name(int tok) {
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
    int tok;
    if (!q_empty()) {
        tok = dequeue();
    } else {
        tok = real_yylex();
    }
    
    // Lookahead: if NEWLINE is followed by DEDENT, emit combined token
    if (tok == NEWLINE && !q_empty() && q_peek() == DEDENT) {
        dequeue(); // Consume the DEDENT from queue
        return NEWLINE_DEDENT;
    }
    
    // if (tok > 0) fprintf(stderr, "TOKEN: %s (%s) at line %d\n", tok_name(tok), yytext, yylineno);
    return tok;
}

#define yylex real_yylex
%}

%option noyywrap
%option yylineno
%option stack

/* Start conditions */
%x BOL
%x FLOW

WS          [ \t]
NEWLINE     \n|\r\n|\r
DIGIT       [0-9]
ALPHA       [a-zA-Z_]
ALNUM       [a-zA-Z0-9_]

/* Simplified SAFE classes - Escape brackets properly */
SAFE_C_BLK  [a-zA-Z0-9_\-./!@#$%&()=+~,\[\]{}]
SAFE_S_BLK  [a-zA-Z0-9_\-./@$+=~]
SAFE_C_FLW  [a-zA-Z0-9_\-./!@#$%&()=+~]
SAFE_S_FLW  [a-zA-Z0-9_\-./@$+=~]

%%

 /* Start in BOL state */
%{
    static int first_call = 1;
    if (first_call) {
        first_call = 0;
        yy_push_state(BOL);
    }
%}

<BOL>[ \t]+             { 
                          int indent = 0;
                          for (int i = 0; i < yyleng; i++) {
                              if (yytext[i] == ' ') indent++;
                              else if (yytext[i] == '\t') indent = (indent + 8) & ~7;
                          }
                          pending_indent = indent;
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

<INITIAL,FLOW>^"%TAG"       { return TAG_DIRECTIVE; }
<INITIAL,FLOW>^"%YAML"      { return YAML_DIRECTIVE; }
<INITIAL,FLOW>^%[^ \t\n]+    { 
                            /* Unknown directive - consume line */
                            int c;
                            while((c = input()) != '\n' && c != EOF);
                            if(c == '\n') return NEWLINE;
                            return 0;
                          }
<INITIAL,FLOW>"---"          { return DOC_START; }
<INITIAL,FLOW>"..."          { return DOC_END; }

<INITIAL,FLOW>("|"|">")([+-]|[0-9]|[+-][0-9]|[0-9][+-])?([ ]*|([ ]*"#"[^\n\r]*)){NEWLINE} { 
                          int base_indent = indent_stack[indent_level];
                          int explicit_indent = 0;
                          int chomp = 0; 
                          // Parse indicators
                          char *p = yytext + 1;
                          while (*p && *p != ' ' && *p != '\n' && *p != '\r' && *p != '#') {
                              if (*p >= '0' && *p <= '9') explicit_indent = *p - '0';
                              else if (*p == '+') chomp = 1;
                              else if (*p == '-') chomp = 2;
                              p++;
                          }

                          int folded = (yytext[0] == '>');
                          int tok = folded ? FOLDED : LITERAL;
                          
                          block_buf_len = 0;
                          if (block_buffer) block_buffer[0] = '\0';
                          
                          int c;
                          int first_line = 1;
                          int detected_indent = -1;
                          
                          while (1) {
                              int indent = 0;
                              int pos = 0;
                              char line_buf[1024];
                              while ((c = input()) == ' ' || c == '\t') {
                                  if (c == ' ') indent++;
                                  else indent = (indent + 8) & ~7;
                                  if (pos < 1023) line_buf[pos++] = c;
                              }
                              if (c == EOF) break;
                              
                              if (c == '\n' || c == '\r') {
                                  if (c == '\r') { int c2 = input(); if (c2 != '\n' && c2 != EOF) unput(c2); }
                                  append_block("\n");
                                  continue;
                              }
                              
                              if (first_line && explicit_indent == 0) {
                                  if (indent <= base_indent) { /* End */ } else { detected_indent = indent; }
                              } else if (first_line && explicit_indent > 0) {
                                  detected_indent = base_indent + explicit_indent;
                              }
                              if (detected_indent == -1) detected_indent = base_indent + 1;
                              
                              if (indent < detected_indent) {
                                  unput(c);
                                  for (int i = pos - 1; i >= 0; i--) unput(line_buf[i]);
                                  break;
                              }
                              first_line = 0;
                              
                              line_buf[pos++] = c;
                              while ((c = input()) != '\n' && c != '\r' && c != EOF) {
                                  if (pos < 1023) line_buf[pos++] = c;
                              }
                              line_buf[pos] = '\0';
                              
                              int skip = (indent > detected_indent) ? detected_indent : indent;
                              append_block(line_buf + skip);
                              append_block("\n");
                              
                              if (c == EOF) break;
                              if (c == '\r') { int c2 = input(); if (c2 != '\n' && c2 != EOF) unput(c2); }
                          }
                          
                          if (chomp == 2) { while (block_buf_len > 0 && block_buffer[block_buf_len-1] == '\n') block_buffer[--block_buf_len] = '\0'; }
                          else if (chomp == 0) { while (block_buf_len > 1 && block_buffer[block_buf_len-1] == '\n' && block_buffer[block_buf_len-2] == '\n') block_buffer[--block_buf_len] = '\0'; }
                          
                          yylval.str = strdup(block_buffer ? block_buffer : "");
                          enqueue(LITERAL_CONTENT);
                          enqueue(NEWLINE);
                          return tok;
                        }

<INITIAL,FLOW>"&"[a-zA-Z0-9_\-]+    { yylval.str = strdup(yytext+1); return ANCHOR; }
<INITIAL,FLOW>"*"[a-zA-Z0-9_\-]+    { yylval.str = strdup(yytext+1); return ALIAS; }
<INITIAL,FLOW>"!"[a-zA-Z0-9_\-./!@#$%&()=+~\\<>]* { yylval.str = strdup(yytext+1); return TAG; }

<INITIAL,FLOW>"#"[^\n\r]*    { /* Comment */ }

<INITIAL>"["            { yy_push_state(FLOW); return LBRACKET; }
<FLOW>"["               { yy_push_state(FLOW); return LBRACKET; }

<INITIAL>"]"            { /* Incorrect in block? but return anyway */ return RBRACKET; }
<FLOW>"]"               { yy_pop_state(); return RBRACKET; }

<INITIAL>"{"            { yy_push_state(FLOW); return LBRACE; }
<FLOW>"{"               { yy_push_state(FLOW); return LBRACE; }

<INITIAL>"}"            { return RBRACE; }
<FLOW>"}"               { yy_pop_state(); return RBRACE; }

<INITIAL,FLOW>","       { return COMMA; }

<INITIAL>"-"/[ \t\n]    { return SEQ_ENTRY; }
<INITIAL>"?"/[ \t\n]    { return MAP_KEY; }
<INITIAL>":"/[ \t\n]    { return COLON; }

<INITIAL>"-"            { REJECT; }

<FLOW>"-"               { yylval.str = strdup("-"); return PLAIN_SCALAR; }
<FLOW>"?"               { return MAP_KEY; }

<INITIAL>{SAFE_S_BLK}{SAFE_C_BLK}* {
    yylval.str = strdup(yytext);
    return PLAIN_SCALAR;
}

<FLOW>{SAFE_S_FLW}{SAFE_C_FLW}* {
    yylval.str = strdup(yytext);
    return PLAIN_SCALAR;
}

<FLOW>":"               { 
                            yylval.str = strdup(":");
                            return PLAIN_SCALAR;
                        }
<FLOW>":"/[ \t\r\n\[\]\{\}\,] {
                            yyless(1); /* Push back the follower */
                            return COLON; 
                        }

<INITIAL,FLOW>\"([^\"\\]|\\.)*\" { 
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return DQUOTE_STRING;
                        }

<INITIAL,FLOW>\'[^\']*\'     {
                          yylval.str = strndup(yytext+1, yyleng-2);
                          return SQUOTE_STRING;
                        }



<INITIAL>{NEWLINE}      { 
                          pending_indent = 0;
                          BEGIN(BOL); 
                          return NEWLINE; 
                        }

<FLOW>{NEWLINE}         { /* Ignore newlines in flow context */ }

<INITIAL,FLOW>[ \t]+         { /* Whitespace */ }

<INITIAL,FLOW>.              { return yytext[0]; }

<INITIAL,FLOW><<EOF>>        {
                          while (indent_level > 0) {
                              indent_level--;
                              enqueue(DEDENT);
                          }
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

%%

#undef yylex
