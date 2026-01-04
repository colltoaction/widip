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
    if (!child) return NULL;
    child->tag = tag;
    return child;
}

Node *make_anchor(char *anchor, Node *child) {
    if (!child) return NULL;
    child->anchor = anchor;
    return child;
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

void print_indent(int depth) {
    for (int i = 0; i < depth * 2; i++) putchar(' ');
}

/* Recursive print that handles logic of anchor/tag wrapping simulation */
void print_node_recursive(Node *n, int depth, int print_anchor, int print_tag) {
    if (!n) return;
    
    if (print_anchor && n->anchor) {
        print_indent(depth);
        printf("ANCHOR: &%s\n", n->anchor);
        print_node_recursive(n, depth + 1, 0, 1);
        return;
    }
    
    if (print_tag && n->tag) {
        print_indent(depth);
        printf("TAG: %s\n", n->tag);
        print_node_recursive(n, depth + 1, 0, 0);
        return;
    }

    print_indent(depth);
    switch (n->type) {
        case NODE_SCALAR:
            printf("SCALAR: %s\n", n->value ? n->value : "(null)");
            break;
        case NODE_SEQ:
            printf("SEQUENCE:\n");
            for (Node *c = n->children; c; c = c->next)
                print_node_recursive(c, depth + 1, 1, 1);
            break;
        case NODE_MAP:
            printf("MAPPING:\n");
            for (Node *c = n->children; c; c = c->next)
                print_node_recursive(c, depth + 1, 1, 1);
            break;
        case NODE_ALIAS:
            printf("ALIAS: *%s\n", n->value);
            break;
        case NODE_STREAM:
            printf("STREAM:\n");
            for (Node *c = n->children; c; c = c->next)
                print_node_recursive(c, depth + 1, 1, 1);
            break;
        case NODE_BLOCK_SCALAR:
            printf("BLOCK: %s\n", n->value);
            break;
        case NODE_NULL:
            printf("SCALAR: null\n");
            break;
    }
}

void print_node(Node *n, int depth) {
    print_node_recursive(n, depth, 1, 1);
}

char *join_scalar_values(char *s1, char *s2) {
    if (!s1) return s2;
    if (!s2) return s1;
    int len = strlen(s1) + strlen(s2) + 2;
    char *new_s = malloc(len);
    sprintf(new_s, "%s %s", s1, s2);
    free(s1);
    free(s2);
    return new_s;
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
%token TAG_DIRECTIVE YAML_DIRECTIVE

%nonassoc LOW_PREC
%nonassoc TAG
%nonassoc DEDENT

%type <node> stream document document_list node optional_node flow_node block_node optional_flow_node
%type <node> flow_seq_items flow_map_entries flow_map_entry
%type <node> block_sequence block_mapping block_seq_items block_map_entries map_entry
%type <node> anchored_node tagged_node anchored_tagged_node
%type <str> merged_plain_scalar

%start stream

/* High precedence for COLON to favor mapping entry reduction over document list repetition */
%right COLON

%%

stream
    : opt_newlines document_list    { root = make_stream($2); }
    | opt_newlines                  { root = make_stream(NULL); }
    ;

document_list
    : document              { $$ = $1; }
    | document_list document{ $$ = append_node($1, $2); }
    ;

document
    : node opt_newlines { $$ = $1; }
    | DOC_START opt_newlines optional_node opt_newlines { $$ = $3; }
    | directives DOC_START opt_newlines optional_node opt_newlines { $$ = $4; }
    | DOC_END opt_newlines { $$ = make_null(); }
    | DOC_START DOC_END opt_newlines { $$ = make_null(); }
    ;

directives
    : directive
    | directives directive
    ;

directive
    : TAG_DIRECTIVE_LINE
    | YAML_DIRECTIVE_LINE
    ;

directive_args
    : PLAIN_SCALAR
    | directive_args PLAIN_SCALAR
    ;

TAG_DIRECTIVE_LINE
    : TAG_DIRECTIVE TAG directive_args NEWLINE { /* Handle TAG directive */ }
    ;

YAML_DIRECTIVE_LINE
    : YAML_DIRECTIVE directive_args NEWLINE { /* Handle YAML directive */ }
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
    | anchored_node
    | tagged_node
    | anchored_tagged_node
    ;

flow_node
    : merged_plain_scalar   { $$ = make_scalar($1); }
    | DQUOTE_STRING         { $$ = make_scalar($1); }
    | SQUOTE_STRING         { $$ = make_scalar($1); }
    | ALIAS                 { $$ = make_alias($1); }
    | LBRACKET flow_seq_items RBRACKET { $$ = make_seq($2); }
    | LBRACKET RBRACKET { $$ = make_seq(NULL); }
    | LBRACE flow_map_entries RBRACE   { $$ = make_map($2); }
    | LBRACE RBRACE { $$ = make_map(NULL); }
    ;

block_node
    : block_sequence        { $$ = $1; }
    | block_mapping         { $$ = $1; }
    | LITERAL LITERAL_CONTENT { $$ = make_block_scalar($2, 0); }
    | FOLDED LITERAL_CONTENT  { $$ = make_block_scalar($2, 1); }
    | INDENT node DEDENT    { $$ = $2; }
    ;

anchored_tagged_node
    : ANCHOR opt_newlines TAG opt_newlines node {
                              $$ = make_anchor($1, make_tag($3, $5));
                            }
    | TAG opt_newlines ANCHOR opt_newlines node {
                              $$ = make_tag($1, make_anchor($3, $5));
                            }
    | ANCHOR opt_newlines TAG opt_newlines {
                              $$ = make_anchor($1, make_tag($3, make_null()));
                            } %prec LOW_PREC
    | TAG opt_newlines ANCHOR opt_newlines {
                              $$ = make_tag($1, make_anchor($3, make_null()));
                            } %prec LOW_PREC
    ;

anchored_node
    : ANCHOR opt_newlines node {
                              $$ = make_anchor($1, $3);
                            }
    | ANCHOR newlines INDENT node DEDENT {
                              $$ = make_anchor($1, $4);
                            }
    | ANCHOR newlines DEDENT node {
                              $$ = make_anchor($1, $4);
                            }
    | ANCHOR opt_newlines {
                              $$ = make_anchor($1, make_null());
                            } %prec LOW_PREC
    ;

merged_plain_scalar
    : PLAIN_SCALAR { $$ = $1; }
    | merged_plain_scalar PLAIN_SCALAR { $$ = join_scalar_values($1, $2); }
    ;

tagged_node
    : TAG opt_newlines node { $$ = make_tag($1, $3); }
    | TAG newlines INDENT node DEDENT { $$ = make_tag($1, $4); }
    | TAG newlines DEDENT node { $$ = make_tag($1, $4); }
    | TAG opt_newlines { $$ = make_tag($1, make_null()); } %prec LOW_PREC
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
    : flow_node COLON opt_newlines optional_node { $$ = append_node($1, $4); }
    | flow_node COLON newlines INDENT node DEDENT { $$ = append_node($1, $5); }
    | MAP_KEY optional_node COLON opt_newlines optional_node { $$ = append_node($2, $5); }
    | MAP_KEY optional_node                 { $$ = append_node($2, make_null()); }
    | MAP_KEY newlines INDENT optional_node DEDENT COLON opt_newlines optional_node { $$ = append_node($4, $8); }
    | MAP_KEY newlines INDENT optional_node DEDENT { $$ = append_node($4, make_null()); }
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
