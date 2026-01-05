%{
/* YAML Parser - LALR-Safe with Cleaned Flow Entries */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int yylineno;
extern char *yytext;
const char* tok_name(int tok);
void yyerror(const char *s);
int yylex(void);

typedef struct Node {
    enum { N_SCALAR, N_SEQ, N_MAP, N_ALIAS, N_STREAM, N_NULL } type;
    char *tag, *anchor, *value;
    struct Node *children, *next;
} Node;

Node *root = NULL;

Node* nnew(int type) {
    Node *n = calloc(1, sizeof(Node)); n->type = type; return n;
}
Node* nscalar(char *v) { Node *n = nnew(N_SCALAR); n->value = v; return n; }
Node* nseq(Node *c) { Node *n = nnew(N_SEQ); n->children = c; return n; }
Node* nmap(Node *c) { Node *n = nnew(N_MAP); n->children = c; return n; }
Node* nalias(char *v) { Node *n = nnew(N_ALIAS); n->value = v; return n; }
Node* nnull() { Node *n = nnew(N_NULL); n->value = strdup("null"); return n; }

Node* napply(Node *n, Node *p) {
    if (!n) n = nnull();
    if (p) { n->anchor = p->anchor; n->tag = p->tag; free(p); }
    return n;
}
Node* nappend(Node *l, Node *i) {
    if (!l) return i;
    Node *c = l; while (c->next) c = c->next;
    c->next = i; return l;
}
void nprint(Node *n, int d, int pa, int pt) {
    if (!n) return;
    if (pa && n->anchor) { for(int i=0;i<d*2;i++)putchar(' '); printf("ANCHOR: &%s\n", n->anchor); nprint(n, d+1, 0, 1); return; }
    if (pt && n->tag) { for(int i=0;i<d*2;i++)putchar(' '); printf("TAG: %s\n", n->tag); nprint(n, d+1, 0, 0); return; }
    if (n->type == N_STREAM) { printf("STREAM:\n"); for(Node *c=n->children;c;c=c->next) nprint(c, d, 1, 1); return; }
    for(int i=0;i<d*2;i++)putchar(' ');
    switch(n->type) {
        case N_SCALAR: printf("SCALAR: %s\n", n->value); break;
        case N_SEQ: printf("SEQUENCE:\n"); for(Node *c=n->children;c;c=c->next) nprint(c, d+1, 1, 1); break;
        case N_MAP: printf("MAPPING:\n"); for(Node *c=n->children;c;c=c->next) nprint(c, d+1, 1, 1); break;
        case N_ALIAS: printf("ALIAS: *%s\n", n->value); break;
        case N_NULL: printf("SCALAR: null\n"); break;
    }
}
char* jscalar(char *s1, char *s2) {
    char *r = malloc(strlen(s1)+strlen(s2)+2); sprintf(r, "%s %s", s1, s2); free(s1); free(s2); return r;
}
%}

%union { char *str; struct Node *node; }
%token DOC_START LBRACKET RBRACKET LBRACE RBRACE COMMA SEQ_ENTRY MAP_KEY COLON NEWLINE INDENT DEDENT NEWLINE_DEDENT NEWLINE_INDENT DOC_END
%token <str> ANCHOR ALIAS TAG PLAIN_SCALAR DQUOTE_STRING SQUOTE_STRING LITERAL_CONTENT
%token LITERAL FOLDED

%nonassoc LOW_PREC
%nonassoc TAG ANCHOR
%nonassoc DEDENT NEWLINE_DEDENT NEWLINE_INDENT
%nonassoc NEWLINE
%right COLON

%type <node> stream document node pair atom map_list seq_list seq_entry properties property indented_node flow_seq_items flow_map_entries flow_entry flow_seq_item flow_node
%type <str> plain

%start stream

%%

stream : /* empty */ { root = nnew(N_STREAM); $$ = root; }
       | stream document { if($2) $1->children = nappend($1->children, $2); $$=$1; }
       | stream NEWLINE { $$=$1; } | stream DEDENT { $$=$1; } | stream NEWLINE_DEDENT { $$=$1; } ;

document : node | DOC_START node { $$ = $2; } | DOC_START { $$ = nnull(); } ;

node : atom %prec LOW_PREC
     | map_list                          { $$ = nmap($1); }
     | seq_list                          { $$ = nseq($1); }
     | indented_node                     { $$ = $1; }
     | LITERAL LITERAL_CONTENT           { $$ = nscalar($2); }
     | FOLDED LITERAL_CONTENT            { $$ = nscalar($2); }
     ;

map_list : pair { $$ = $1; }
         | map_list NEWLINE pair { $$ = nappend($1, $3); } ;

pair : atom COLON node { $$ = nappend($1, $3); }
     | atom COLON { $$ = nappend($1, nnull()); } %prec LOW_PREC
     | MAP_KEY node COLON node { $$ = nappend($2, $4); }
     | MAP_KEY node { $$ = nappend($2, nnull()); } %prec LOW_PREC ;

atom : flow_node | properties flow_node { $$ = napply($2, $1); }
     | properties %prec LOW_PREC { $$ = napply(NULL, $1); } ;

seq_list : seq_entry { $$ = $1; }
         | seq_list NEWLINE seq_entry { $$ = nappend($1, $3); } ;

seq_entry : SEQ_ENTRY node { $$ = $2; } | SEQ_ENTRY { $$ = nnull(); } ;

indented_node : INDENT node DEDENT { $$ = $2; } | INDENT node NEWLINE_DEDENT { $$ = $2; }
              | NEWLINE_INDENT node DEDENT { $$ = $2; } | NEWLINE_INDENT node NEWLINE_DEDENT { $$ = $2; } ;

flow_node : plain { $$ = nscalar($1); } | DQUOTE_STRING { $$ = nscalar($1); } | SQUOTE_STRING { $$ = nscalar($1); }
          | ALIAS { $$ = nalias($1); }
          | LBRACE flow_map_entries RBRACE { $$ = nmap($2); } | LBRACE RBRACE { $$ = nmap(NULL); }
          | LBRACKET flow_seq_items RBRACKET { $$ = nseq($2); } | LBRACKET RBRACKET { $$ = nseq(NULL); }
          ;

plain : PLAIN_SCALAR | plain PLAIN_SCALAR { $$ = jscalar($1, $2); } ;

flow_seq_items : flow_seq_item { $$ = $1; } | flow_seq_items COMMA flow_seq_item { $$ = nappend($1, $3); } | flow_seq_items COMMA { $$ = nappend($1, nnull()); } ;
flow_seq_item : node %prec LOW_PREC { $$ = $1; } ;

flow_map_entries : flow_entry { $$ = $1; } | flow_map_entries COMMA flow_entry { $$ = nappend($1, $3); } | flow_map_entries COMMA { $$ = $1; } ;
flow_entry : pair | atom { $$ = nappend($1, nnull()); } %prec LOW_PREC ;

properties : property | properties property { if($2->anchor) $1->anchor = $2->anchor; if($2->tag) $1->tag = $2->tag; free($2); $$ = $1; } ;
property : ANCHOR { $$ = nnew(0); $$->anchor = $1; } | TAG { $$ = nnew(0); $$->tag = $1; } ;

%%
void yyerror(const char *s) { fprintf(stderr, "Error line %d: %s (tok: %s, text: '%s')\n", yylineno, s, tok_name(yychar), yytext); }
int main() { if (!yyparse() && root) { nprint(root, 0, 1, 1); return 0; } return 1; }
