%{
/* YAML Parser - Native LALR Version */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char* tok_name(int tok);
void yyerror(const char *s);
int yylex(void);

typedef enum {
    NODE_SCALAR, NODE_SEQ, NODE_MAP, NODE_ALIAS, NODE_STREAM, NODE_BLOCK_SCALAR, NODE_NULL
} NodeType;

typedef struct Node {
    NodeType type;
    char *tag; char *anchor; char *value;
    struct Node *children; struct Node *next;
} Node;

Node *root = NULL;

Node *make_scalar(char *val) {
    Node *n = (Node*)malloc(sizeof(Node)); n->type = NODE_SCALAR;
    n->tag = NULL; n->anchor = NULL; n->value = val;
    n->children = NULL; n->next = NULL; return n;
}
Node *make_seq(Node *items) {
    Node *n = (Node*)malloc(sizeof(Node)); n->type = NODE_SEQ;
    n->tag = NULL; n->anchor = NULL; n->value = NULL;
    n->children = items; n->next = NULL; return n;
}
Node *make_map(Node *pairs) {
    Node *n = (Node*)malloc(sizeof(Node)); n->type = NODE_MAP;
    n->tag = NULL; n->anchor = NULL; n->value = NULL;
    n->children = pairs; n->next = NULL; return n;
}
Node *make_alias(char *name) {
    Node *n = (Node*)malloc(sizeof(Node)); n->type = NODE_ALIAS;
    n->tag = NULL; n->anchor = NULL; n->value = name;
    n->children = NULL; n->next = NULL; return n;
}
Node *make_null() {
    Node *n = (Node*)malloc(sizeof(Node)); n->type = NODE_NULL;
    n->tag = NULL; n->anchor = NULL; n->value = strdup("null");
    n->children = NULL; n->next = NULL; return n;
}
Node *apply_properties(Node *n, Node *props) {
    if (!n) n = make_null();
    if (props) {
        if (props->anchor) n->anchor = props->anchor;
        if (props->tag) n->tag = props->tag;
        free(props);
    }
    return n;
}
Node *append_node(Node *list, Node *item) {
    if (!list) return item;
    Node *curr = list; while (curr->next) curr = curr->next;
    curr->next = item; return list;
}
void print_indent(int depth) { for (int i = 0; i < depth * 2; i++) putchar(' '); }
void print_node_recursive(Node *n, int depth, int print_anchor, int print_tag) {
    if (!n) return;
    if (print_anchor && n->anchor) {
        print_indent(depth); printf("ANCHOR: &%s\n", n->anchor);
        print_node_recursive(n, depth + 1, 0, 1); return;
    }
    if (print_tag && n->tag) {
        print_indent(depth); printf("TAG: %s\n", n->tag);
        print_node_recursive(n, depth + 1, 0, 0); return;
    }
    if (n->type == NODE_STREAM) {
        printf("STREAM:\n");
        for (Node *c = n->children; c; c = c->next) print_node_recursive(c, depth, 1, 1);
        return;
    }
    print_indent(depth);
    switch (n->type) {
        case NODE_SCALAR: printf("SCALAR: %s\n", n->value); break;
        case NODE_SEQ: printf("SEQUENCE:\n"); for (Node *c = n->children; c; c = c->next) print_node_recursive(c, depth + 1, 1, 1); break;
        case NODE_MAP: printf("MAPPING:\n"); for (Node *c = n->children; c; c = c->next) print_node_recursive(c, depth + 1, 1, 1); break;
        case NODE_ALIAS: printf("ALIAS: *%s\n", n->value); break;
        case NODE_BLOCK_SCALAR: printf("BLOCK: %s\n", n->value); break;
        case NODE_NULL: printf("SCALAR: null\n"); break;
    }
}
char *join_scalar(char *s1, char *s2) {
    if (!s1) return s2; if (!s2) return s1;
    char *res = (char*)malloc(strlen(s1) + strlen(s2) + 2);
    sprintf(res, "%s %s", s1, s2); free(s1); free(s2); return res;
}
%}

%union { char *str; struct Node *node; }
%token DOC_START DOC_END LBRACKET RBRACKET LBRACE RBRACE COMMA SEQ_ENTRY MAP_KEY COLON NEWLINE INDENT DEDENT NEWLINE_DEDENT
%token <str> ANCHOR ALIAS TAG PLAIN_SCALAR DQUOTE_STRING SQUOTE_STRING LITERAL_CONTENT
%token LITERAL FOLDED

%nonassoc LOW_PREC
%nonassoc TAG ANCHOR
%nonassoc DEDENT NEWLINE_DEDENT
%nonassoc NEWLINE
%nonassoc DOC_START DOC_END

%type <node> stream document node flow_node block_node content flow_seq_items flow_map_entries flow_entry flow_seq_item block_sequence block_mapping map_entry entry_key entry_value properties property indented_node
%type <str> merged_plain_scalar

%start stream
%right COLON

%%

newlines: NEWLINE | newlines NEWLINE | NEWLINE_DEDENT | newlines NEWLINE_DEDENT ;
opt_newlines: /* empty */ | newlines ;

stream
    : /* empty */                       { root = (Node*)malloc(sizeof(Node)); root->type=NODE_STREAM; root->children=NULL; $$=root; }
    | stream document                   { if($2) $1->children = append_node($1->children, $2); $$=$1; }
    | stream newlines                   { $$=$1; }
    | stream DEDENT                     { $$=$1; }
    ;

document
    : node                              { $$ = $1; }
    | DOC_START opt_newlines node       { $$ = $3; }
    | DOC_START opt_newlines            { $$ = make_null(); }
    | DOC_START DOC_END                 { $$ = make_null(); }
    | DOC_END                           { $$ = make_null(); }
    ;

node
    : content                           { $$ = $1; }
    | properties content                { $$ = apply_properties($2, $1); }
    | properties opt_newlines indented_node { $$ = apply_properties($3, $1); }
    | properties %prec LOW_PREC         { $$ = apply_properties(NULL, $1); }
    ;

indented_node
    : INDENT node DEDENT                { $$ = $2; }
    | INDENT node NEWLINE_DEDENT         { $$ = $2; }
    ;

content : flow_node | block_node ;

properties
    : property                          { $$ = $1; }
    | properties property               { if($2->anchor) $1->anchor = $2->anchor; if($2->tag) $1->tag = $2->tag; free($2); $$=$1; }
    ;

property
    : ANCHOR { $$=(Node*)malloc(sizeof(Node)); $$->anchor=$1; $$->tag=NULL; }
    | TAG    { $$=(Node*)malloc(sizeof(Node)); $$->tag=$1; $$->anchor=NULL; }
    ;

flow_node
    : merged_plain_scalar               { $$ = make_scalar($1); }
    | DQUOTE_STRING                     { $$ = make_scalar($1); }
    | SQUOTE_STRING                     { $$ = make_scalar($1); }
    | ALIAS                             { $$ = make_alias($1); }
    | LBRACE flow_map_entries RBRACE    { $$ = make_map($2); }
    | LBRACE RBRACE                     { $$ = make_map(NULL); }
    | LBRACKET flow_seq_items RBRACKET   { $$ = make_seq($2); }
    | LBRACKET RBRACKET                 { $$ = make_seq(NULL); }
    ;

block_node : block_sequence | block_mapping
    | LITERAL LITERAL_CONTENT { Node* n=(Node*)malloc(sizeof(Node)); n->type=NODE_BLOCK_SCALAR; n->value=$2; n->children=n->next=NULL; n->anchor=n->tag=NULL; $$=n; }
    | FOLDED LITERAL_CONTENT  { Node* n=(Node*)malloc(sizeof(Node)); n->type=NODE_BLOCK_SCALAR; n->value=$2; n->children=n->next=NULL; n->anchor=n->tag=NULL; $$=n; }
    ;

merged_plain_scalar : PLAIN_SCALAR { $$=$1; } | merged_plain_scalar PLAIN_SCALAR { $$=join_scalar($1,$2); } ;

flow_seq_items : flow_seq_item { $$=$1; } | flow_seq_items COMMA flow_seq_item { $$=append_node($1,$3); } | flow_seq_items COMMA { $$=append_node($1,make_null()); } ;
flow_seq_item : node %prec LOW_PREC { $$=$1; } | node entry_value { $$=make_map(append_node($1,$2)); } ;
flow_map_entries : flow_entry | flow_map_entries COMMA flow_entry { $$=append_node($1,$3); } | flow_map_entries COMMA { $$=$1; } ;
flow_entry : map_entry | node { $$=append_node($1,make_null()); } ;

block_sequence
    : SEQ_ENTRY node                    { $$ = make_seq($2); }
    | SEQ_ENTRY                         { $$ = make_seq(make_null()); }
    | block_sequence NEWLINE SEQ_ENTRY node { append_node($1->children, $4); $$ = $1; }
    | block_sequence NEWLINE SEQ_ENTRY      { append_node($1->children, make_null()); $$ = $1; }
    | block_sequence NEWLINE_DEDENT SEQ_ENTRY node { append_node($1->children, $4); $$ = $1; }
    | block_sequence NEWLINE_DEDENT SEQ_ENTRY      { append_node($1->children, make_null()); $$ = $1; }
    ;

block_mapping
    : map_entry { $$ = make_map($1); }
    | block_mapping NEWLINE map_entry { append_node($1->children, $3); $$ = $1; }
    | block_mapping NEWLINE_DEDENT map_entry { append_node($1->children, $3); $$ = $1; }
    ;

map_entry : node entry_value { $$=append_node($1,$2); } | entry_key opt_newlines { $$=append_node($1,make_null()); } | entry_key entry_value { $$=append_node($1,$2); } ;
entry_key : MAP_KEY node { $$=$2; } | MAP_KEY { $$=make_null(); } | MAP_KEY newlines indented_node { $$=$3; } ;

entry_value : COLON node { $$=$2; } | COLON { $$=make_null(); } | COLON newlines indented_node { $$=$3; } ;

%%
void yyerror(const char *s) { extern int yylineno; extern char *yytext; extern int yychar; fprintf(stderr, "Parse error at line %d: %s (token: %s, text: '%s')\n", yylineno, s, (yychar > 0 ? tok_name(yychar) : "EOF"), yytext); }
int main(void) { if (yyparse() == 0 && root) { print_node_recursive(root, 0, 1, 1); return 0; } return 1; }
