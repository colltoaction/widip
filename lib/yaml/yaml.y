%{
/* YAML 1.2 Parser - Flexible */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void yyerror(const char *s);
int yylex(void);

/* AST Node Types */
typedef enum {
    NODE_SCALAR,
    NODE_SEQ,
    NODE_MAP,
    NODE_ALIAS,
    NODE_ANCHOR,
    NODE_TAG,
    NODE_STREAM,
    NODE_NULL
} NodeType;

typedef struct Node {
    NodeType type;
    char *tag;
    char *anchor;
    char *value;
    struct Node *children;
    struct Node *next;
} Node;

Node *root = NULL;

Node *make_scalar(char *val) {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_SCALAR;
    n->tag = NULL;
    n->anchor = NULL;
    n->value = val;
    n->children = NULL;
    n->next = NULL;
    return n;
}

Node *make_seq(Node *items) {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_SEQ;
    n->tag = NULL;
    n->anchor = NULL;
    n->value = NULL;
    n->children = items;
    n->next = NULL;
    return n;
}

Node *make_map(Node *pairs) {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_MAP;
    n->tag = NULL;
    n->anchor = NULL;
    n->value = NULL;
    n->children = pairs;
    n->next = NULL;
    return n;
}

Node *make_alias(char *name) {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_ALIAS;
    n->tag = NULL;
    n->anchor = NULL;
    n->value = name;
    n->children = NULL;
    n->next = NULL;
    return n;
}

Node *make_tag(char *tag, Node *child) {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_TAG;
    n->tag = tag;
    n->anchor = NULL;
    n->value = NULL;
    n->children = child;
    n->next = NULL;
    return n;
}

Node *make_stream(Node *docs) {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_STREAM;
    n->tag = NULL;
    n->anchor = NULL;
    n->value = NULL;
    n->children = docs;
    n->next = NULL;
    return n;
}

Node *make_null() {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_SCALAR;
    n->tag = NULL;
    n->anchor = NULL;
    n->value = strdup("null");
    n->children = NULL;
    n->next = NULL;
    return n;
}

Node *append_node(Node *list, Node *item) {
    if (!list) return item;
    Node *curr = list;
    while (curr->next) curr = curr->next;
    curr->next = item;
    return list;
}

void print_node(Node *n, int depth);
void print_indent(int depth) {
    for (int i = 0; i < depth * 2; i++) putchar(' ');
}

void print_node(Node *n, int depth) {
    if (!n) return;
    print_indent(depth);
    switch (n->type) {
        case NODE_SCALAR:
            printf("SCALAR: %s\n", n->value ? n->value : "(null)");
            break;
        case NODE_SEQ:
            printf("SEQUENCE:\n");
            for (Node *c = n->children; c; c = c->next)
                print_node(c, depth + 1);
            break;
        case NODE_MAP:
            printf("MAPPING:\n");
            for (Node *c = n->children; c; c = c->next)
                print_node(c, depth + 1);
            break;
        case NODE_ALIAS:
            printf("ALIAS: *%s\n", n->value);
            break;
        case NODE_ANCHOR:
            printf("ANCHOR: &%s\n", n->anchor);
            print_node(n->children, depth + 1);
            break;
        case NODE_TAG:
            printf("TAG: %s\n", n->tag);
            print_node(n->children, depth + 1);
            break;
        case NODE_STREAM:
            printf("STREAM:\n");
            for (Node *c = n->children; c; c = c->next)
                print_node(c, depth + 1);
            break;
        case NODE_NULL:
            printf("SCALAR: null\n");
            break;
    }
}

%}

%union {
    char *str;
    struct Node *node;
}

%token DOC_START DOC_END
%token LBRACKET RBRACKET LBRACE RBRACE COMMA
%token SEQ_ENTRY MAP_KEY COLON
%token NEWLINE INDENT DEDENT

%token <str> ANCHOR ALIAS TAG
%token <str> PLAIN_SCALAR DQUOTE_STRING SQUOTE_STRING

%type <node> stream document node scalar optional_node
%type <node> flow_sequence flow_mapping flow_seq_items flow_map_entries
%type <node> block_sequence block_mapping block_seq_items block_map_entries
%type <node> tagged_node anchored_node document_list

%start stream

%%

stream
    : document_list         { root = make_stream($1); }
    | opt_newlines          { root = make_stream(NULL); }
    ;

document_list
    : document              { $$ = $1; }
    | document_list document{ $$ = append_node($1, $2); }
    ;

document
    : node opt_newlines { $$ = $1; }
    | DOC_START opt_newlines optional_node opt_newlines       { $$ = $3; }
    | DOC_START opt_newlines optional_node opt_newlines DOC_END opt_newlines { $$ = $3; }
    | DOC_END opt_newlines { $$ = make_null(); }
    ;

opt_newlines
    : /* empty */
    | newlines
    ;

newlines
    : NEWLINE
    | newlines NEWLINE
    | newlines INDENT DEDENT
    ;

node
    : scalar                { $$ = $1; }
    | flow_sequence         { $$ = $1; }
    | flow_mapping          { $$ = $1; }
    | block_sequence        { $$ = $1; }
    | block_mapping         { $$ = $1; }
    | tagged_node           { $$ = $1; }
    | anchored_node         { $$ = $1; }
    | ALIAS                 { $$ = make_alias($1); }
    ;

optional_node
    : node { $$ = $1; }
    | /* empty */ { $$ = make_null(); }
    ;

scalar
    : PLAIN_SCALAR          { $$ = make_scalar($1); }
    | DQUOTE_STRING         { $$ = make_scalar($1); }
    | SQUOTE_STRING         { $$ = make_scalar($1); }
    ;

tagged_node
    : TAG opt_newlines node { $$ = make_tag($1, $3); }
    ;

anchored_node
    : ANCHOR opt_newlines node { 
                              $$ = malloc(sizeof(Node));
                              $$->type = NODE_ANCHOR;
                              $$->anchor = $1;
                              $$->children = $3;
                              $$->next = NULL;
                            }
    ;

/* Flow Sequence: [a, b, c] */
flow_sequence
    : LBRACKET RBRACKET                     { $$ = make_seq(NULL); }
    | LBRACKET flow_seq_items RBRACKET      { $$ = make_seq($2); }
    ;

flow_seq_items
    : optional_node                         { $$ = $1; }
    | flow_seq_items COMMA optional_node    { $$ = append_node($1, $3); }
    ;

/* Flow Mapping: {key: value} */
flow_mapping
    : LBRACE RBRACE                         { $$ = make_map(NULL); }
    | LBRACE flow_map_entries RBRACE        { $$ = make_map($2); }
    ;

flow_map_entries
    : node COLON optional_node              { $$ = append_node($1, $3); }
    | flow_map_entries COMMA node COLON optional_node{ $$ = append_node($1, append_node($3, $5)); }
    | flow_map_entries COMMA                { $$ = $1; }
    ;

/* Block Sequence: - item */
block_sequence
    : block_seq_items                       { $$ = make_seq($1); }
    | INDENT block_seq_items DEDENT         { $$ = make_seq($2); }
    ;

block_seq_items
    : SEQ_ENTRY optional_node               { $$ = $2; }
    | block_seq_items opt_newlines SEQ_ENTRY optional_node{ $$ = append_node($1, $4); }
    ;

/* Block Mapping: key: value */
block_mapping
    : block_map_entries                     { $$ = make_map($1); }
    | INDENT block_map_entries DEDENT         { $$ = make_map($2); }
    ;

block_map_entries
    : node COLON opt_newlines optional_node     { $$ = append_node($1, $4); }
    | MAP_KEY node COLON opt_newlines optional_node { $$ = append_node($2, $5); }
    | MAP_KEY node { $$ = append_node($2, make_null()); }
    | block_map_entries opt_newlines node COLON opt_newlines optional_node
                                            { $$ = append_node($1, append_node($3, $6)); }
    | block_map_entries opt_newlines MAP_KEY node COLON opt_newlines optional_node
                                            { $$ = append_node($1, append_node($4, $7)); }
    | block_map_entries opt_newlines MAP_KEY node { $$ = append_node($1, append_node($4, make_null())); }
    ;

%%

void yyerror(const char *s) {
    extern int yylineno;
    fprintf(stderr, "Parse error at line %d: %s\n", yylineno, s);
}

int main(int argc, char **argv) {
    if (yyparse() == 0 && root) {
        print_node(root, 0);
        return 0;
    }
    return 1;
}
