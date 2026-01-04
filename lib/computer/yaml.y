%{
/* YAML 1.2 Parser - Simplified Subset */
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
    NODE_TAG
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
%token NEWLINE

%token <str> ANCHOR ALIAS TAG
%token <str> PLAIN_SCALAR DQUOTE_STRING SQUOTE_STRING

%type <node> stream document node scalar
%type <node> flow_sequence flow_mapping flow_seq_items flow_map_entries
%type <node> block_sequence block_mapping block_seq_items block_map_entries
%type <node> tagged_node anchored_node document_list

%start stream

%%

stream
    : document_list         { root = make_seq($1); }
    ;

document_list
    : document              { $$ = $1; }
    | document_list document{ $$ = append_node($1, $2); }
    ;

document
    : node optional_newlines { $$ = $1; }
    | DOC_START optional_newlines node        { $$ = $3; }
    | DOC_START optional_newlines node DOC_END{ $$ = $3; }
    | newlines node optional_newlines { $$ = $2; }
    ;

optional_newlines
    : /* empty */
    | newlines
    ;

newlines
    : NEWLINE
    | newlines NEWLINE
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

scalar
    : PLAIN_SCALAR          { $$ = make_scalar($1); }
    | DQUOTE_STRING         { $$ = make_scalar($1); }
    | SQUOTE_STRING         { $$ = make_scalar($1); }
    ;

tagged_node
    : TAG optional_newlines node { $$ = make_tag($1, $3); }
    ;

anchored_node
    : ANCHOR optional_newlines node { 
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
    : node                                  { $$ = $1; }
    | flow_seq_items COMMA node             { $$ = append_node($1, $3); }
    | flow_seq_items COMMA                  { $$ = $1; /* trailing comma */ }
    ;

/* Flow Mapping: {key: value} */
flow_mapping
    : LBRACE RBRACE                         { $$ = make_map(NULL); }
    | LBRACE flow_map_entries RBRACE        { $$ = make_map($2); }
    ;

flow_map_entries
    : node COLON node                       { $$ = append_node($1, $3); }
    | flow_map_entries COMMA node COLON node{ $$ = append_node($1, append_node($3, $5)); }
    | flow_map_entries COMMA                { $$ = $1; }
    ;

/* Block Sequence: - item */
block_sequence
    : block_seq_items                       { $$ = make_seq($1); }
    ;

block_seq_items
    : SEQ_ENTRY node                        { $$ = $2; }
    | block_seq_items newlines SEQ_ENTRY node{ $$ = append_node($1, $4); }
    | block_seq_items newlines               { $$ = $1; }
    ;

/* Block Mapping: key: value */
block_mapping
    : block_map_entries                     { $$ = make_map($1); }
    ;

block_map_entries
    : node COLON optional_newlines node     { $$ = append_node($1, $4); }
    | block_map_entries newlines node COLON optional_newlines node
                                            { $$ = append_node($1, append_node($3, $6)); }
    | block_map_entries newlines             { $$ = $1; }
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
