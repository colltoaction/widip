%{
/* YAML 1.2 Lexer - Final Polish */
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

void enqueue(int t) { 
    if (q_tail < 2048) token_queue[q_tail++] = t; 
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
        case TAG_DIRECTIVE: return "TAG_DIRECTIVE";
        case YAML_DIRECTIVE: return "YAML_DIRECTIVE";
        default: return "OTHER";
    }
}

int yylex() {
    int tok;
    while (1) {
        if (!q_empty()) tok = dequeue();
        else tok = real_yylex();
        
        if (tok == 0 && q_empty()) return 0;
        
        if (tok == NEWLINE && !q_empty() && q_peek() == DEDENT) {
            dequeue();
            return NEWLINE_DEDENT;
        }
        
        if (tok != 0) {
            if (!q_empty()) {
                enqueue(tok);
                return dequeue();
            }
            return tok;
        }
    }
}

#define yylex real_yylex
%}

%option noyywrap
%option yylineno
%option stack

%x BOL
%x FLOW

NEWLINE     \n|\r\n|\r
SAFE_S_BLK  [^ \t\n\-\?:,\[\]\{\}!#&*|>\x22\x27]
SAFE_C_BLK  [^ \t\n\-\?:,\[\]\{\}!#&*|>\x22\x27]

%%

%{
    static int first_init = 1;
    if (first_init) { first_init = 0; BEGIN(BOL); }
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
                          while (indent_level > 0) { indent_level--; enqueue(DEDENT); }
                          enqueue(DEDENT); 
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

<INITIAL,FLOW>"---"/([ \t\n\r]|$)   { return DOC_START; }
<INITIAL,FLOW>"..."/([ \t\n\r]|$)   { return DOC_END; }

<INITIAL>"-"/([ \t\n\r]|$)           { return SEQ_ENTRY; }
<INITIAL>":"/([ \t\n\r]|$)           { return COLON; }
<INITIAL>"?"/([ \t\n\r]|$)           { return MAP_KEY; }

<INITIAL,FLOW>","       { return COMMA; }
<INITIAL,FLOW>"["       { flow_level++; yy_push_state(FLOW); return LBRACKET; }
<FLOW>"]"               { if (flow_level > 0) flow_level--; yy_pop_state(); return RBRACKET; }
<INITIAL,FLOW>"{"       { flow_level++; yy_push_state(FLOW); return LBRACE; }
<FLOW>"}"               { if (flow_level > 0) flow_level--; yy_pop_state(); return RBRACE; }

<FLOW>"-"               { yylval.str = strdup("-"); return PLAIN_SCALAR; }
<FLOW>":"               { return COLON; }
<FLOW>"?"               { return MAP_KEY; }

<INITIAL,FLOW>"&"[a-zA-Z0-9_\-]+    { yylval.str = strdup(yytext+1); return ANCHOR; }
<INITIAL,FLOW>"*"[a-zA-Z0-9_\-]+    { yylval.str = strdup(yytext+1); return ALIAS; }

<INITIAL,FLOW>"!"[a-zA-Z0-9_\-./!@#$%&()=+~\\<>]+ { 
    yylval.str = strdup(yytext+1); 
    return TAG; 
}
<INITIAL,FLOW>"!"                   { 
    yylval.str = strdup(""); 
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

<INITIAL,FLOW>{SAFE_S_BLK}{SAFE_C_BLK}* {
    yylval.str = strdup(yytext);
    return PLAIN_SCALAR;
}

<INITIAL,FLOW>"#"[^\n\r]*    { /* ignore */ }

<INITIAL>{NEWLINE}      { 
                          if (flow_level == 0) {
                              int c;
                              int next_indent = 0;
                              int pc[128];
                              int pcc = 0;
                              while (pcc < 127 && ((c = input()) == ' ' || c == '\t')) {
                                  pc[pcc++] = c;
                                  if (c == ' ') next_indent++;
                                  else if (c == '\t') next_indent = (next_indent + 8) & ~7;
                              }
                              if ((c == EOF || c == 0) || (c != '\n' && c != '\r' && next_indent < indent_stack[indent_level])) {
                                  if (c == EOF || c == 0) {
                                      while(indent_level >= 0) { indent_level--; enqueue(DEDENT); }
                                  } else {
                                      while (next_indent < indent_stack[indent_level] && indent_level > 0) {
                                          indent_level--; enqueue(DEDENT);
                                      }
                                  }
                              }
                              if (c != EOF && c != 0) unput(c);
                              for (int i = pcc - 1; i >= 0; i--) unput(pc[i]);
                          }
                          BEGIN(BOL); 
                          return NEWLINE; 
                        }

<FLOW>{NEWLINE}         { /* ignore */ }

[ \t]+                  { /* ignore */ }

.                       { return yytext[0]; }

<<EOF>>                 {
                          while (indent_level >= 0) {
                              indent_level--;
                              enqueue(DEDENT);
                          }
                          if (!q_empty()) return dequeue();
                          return 0;
                        }

%%

#undef yylex
