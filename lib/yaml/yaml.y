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
    NODE_BLOCK_SCALAR,
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

Node *make_block_scalar(char *val, int folded) {
    Node *n = malloc(sizeof(Node));
    n->type = NODE_BLOCK_SCALAR;
    n->tag = NULL;
    n->anchor = NULL;
    n->value = val;
    n->children = NULL;
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
        case NODE_BLOCK_SCALAR:
            printf("BLOCK: %s\n", n->value);
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
%token <str> PLAIN_SCALAR DQUOTE_STRING SQUOTE_STRING LITERAL_CONTENT
%token LITERAL FOLDED

%type <node> stream document document_list node optional_node flow_node block_node optional_flow_node
%type <node> flow_seq_items flow_map_entries flow_map_entry
%type <node> block_sequence block_mapping block_seq_items block_map_entries map_entry

%start stream

/* High precedence for COLON to favor mapping entry reduction over document list repetition */
%right COLON

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
    | DOC_START opt_newlines optional_node opt_newlines { $$ = $3; }
    ;

opt_newlines
    : /* empty */
    | newlines
    ;

newlines
    : NEWLINE
    | newlines NEWLINE
    ;

optional_node
    : node { $$ = $1; }
    | /* empty */ { $$ = make_null(); }
    ;

optional_flow_node
    : flow_node { $$ = $1; }
    | /* empty */ { $$ = make_null(); }
    ;

node
    : flow_node
    | block_node
    ;

flow_node
    : PLAIN_SCALAR          { $$ = make_scalar($1); }
    | DQUOTE_STRING         { $$ = make_scalar($1); }
    | SQUOTE_STRING         { $$ = make_scalar($1); }
    | ALIAS                 { $$ = make_alias($1); }
    | LBRACKET flow_seq_items RBRACKET { $$ = make_seq($2); }
    | LBRACE flow_map_entries RBRACE   { $$ = make_map($2); }
    | TAG opt_newlines flow_node { $$ = make_tag($1, $3); }
    | ANCHOR opt_newlines flow_node { 
                              $$ = malloc(sizeof(Node));
                              $$->type = NODE_ANCHOR;
                              $$->anchor = $1;
                              $$->children = $3;
                              $$->next = NULL;
                            }
    ;

block_node
    : block_sequence        { $$ = $1; }
    | block_mapping         { $$ = $1; }
    | LITERAL LITERAL_CONTENT { $$ = make_block_scalar($2, 0); }
    | FOLDED LITERAL_CONTENT  { $$ = make_block_scalar($2, 1); }
    | TAG opt_newlines block_node { $$ = make_tag($1, $3); }
    | ANCHOR opt_newlines block_node { 
                              $$ = malloc(sizeof(Node));
                              $$->type = NODE_ANCHOR;
                              $$->anchor = $1;
                              $$->children = $3;
                              $$->next = NULL;
                            }
    | INDENT node DEDENT    { $$ = $2; }
    ;

flow_seq_items
    : optional_flow_node                         { $$ = $1; }
    | flow_seq_items COMMA optional_flow_node    { $$ = append_node($1, $3); }
    ;

flow_map_entries
    : flow_map_entry                        { $$ = $1; }
    | flow_map_entries COMMA flow_map_entry { $$ = append_node($1, $3); }
    | flow_map_entries COMMA                { $$ = $1; }
    ;

flow_map_entry
    : flow_node COLON optional_flow_node              { $$ = append_node($1, $3); }
    | flow_node                                       { $$ = append_node($1, make_null()); }
    | MAP_KEY optional_flow_node COLON optional_flow_node { $$ = append_node($2, $4); }
    | MAP_KEY optional_flow_node                      { $$ = append_node($2, make_null()); }
    ;

block_sequence
    : block_seq_items opt_newlines          { $$ = make_seq($1); }
    ;

block_seq_items
    : SEQ_ENTRY optional_node               { $$ = $2; }
    | block_seq_items opt_newlines SEQ_ENTRY optional_node{ $$ = append_node($1, $4); }
    ;

block_mapping
    : block_map_entries opt_newlines            { $$ = make_map($1); }
    ;

/* Block mapping entries - key: value pairs at same indentation */
block_map_entries
    : map_entry                             { $$ = $1; }
    | block_map_entries newlines map_entry  { $$ = append_node($1, $3); }
    ;

/* A single mapping entry: key: value (value can be inline or on next line indented) */
map_entry
    : node COLON opt_newlines optional_node { $$ = append_node($1, $4); }
    | node COLON newlines INDENT node DEDENT { $$ = append_node($1, $5); }
    | MAP_KEY optional_node COLON opt_newlines optional_node { $$ = append_node($2, $5); }
    | MAP_KEY optional_node                 { $$ = append_node($2, make_null()); }
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
