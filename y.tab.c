/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison implementation for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* C LALR(1) parser skeleton written by Richard Stallman, by
   simplifying the original so-called "semantic" parser.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

/* All symbols defined below should begin with yy or YY, to avoid
   infringing on user name space.  This should be done even for local
   variables, as they might otherwise be expanded by user macros.
   There are some unavoidable exceptions within include files to
   define necessary library symbols; they are noted "INFRINGES ON
   USER NAME SPACE" below.  */

/* Identify Bison output, and Bison version.  */
#define YYBISON 30802

/* Bison version string.  */
#define YYBISON_VERSION "3.8.2"

/* Skeleton name.  */
#define YYSKELETON_NAME "yacc.c"

/* Pure parsers.  */
#define YYPURE 0

/* Push parsers.  */
#define YYPUSH 0

/* Pull parsers.  */
#define YYPULL 1




/* First part of user prologue.  */
#line 1 "lib/yaml/yaml.y"

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


#line 270 "y.tab.c"

# ifndef YY_CAST
#  ifdef __cplusplus
#   define YY_CAST(Type, Val) static_cast<Type> (Val)
#   define YY_REINTERPRET_CAST(Type, Val) reinterpret_cast<Type> (Val)
#  else
#   define YY_CAST(Type, Val) ((Type) (Val))
#   define YY_REINTERPRET_CAST(Type, Val) ((Type) (Val))
#  endif
# endif
# ifndef YY_NULLPTR
#  if defined __cplusplus
#   if 201103L <= __cplusplus
#    define YY_NULLPTR nullptr
#   else
#    define YY_NULLPTR 0
#   endif
#  else
#   define YY_NULLPTR ((void*)0)
#  endif
# endif

/* Use api.header.include to #include this header
   instead of duplicating it here.  */
#ifndef YY_YY_Y_TAB_H_INCLUDED
# define YY_YY_Y_TAB_H_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif

/* Token kinds.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    YYEMPTY = -2,
    YYEOF = 0,                     /* "end of file"  */
    YYerror = 256,                 /* error  */
    YYUNDEF = 257,                 /* "invalid token"  */
    DOC_START = 258,               /* DOC_START  */
    DOC_END = 259,                 /* DOC_END  */
    LBRACKET = 260,                /* LBRACKET  */
    RBRACKET = 261,                /* RBRACKET  */
    LBRACE = 262,                  /* LBRACE  */
    RBRACE = 263,                  /* RBRACE  */
    COMMA = 264,                   /* COMMA  */
    SEQ_ENTRY = 265,               /* SEQ_ENTRY  */
    MAP_KEY = 266,                 /* MAP_KEY  */
    COLON = 267,                   /* COLON  */
    NEWLINE = 268,                 /* NEWLINE  */
    INDENT = 269,                  /* INDENT  */
    DEDENT = 270,                  /* DEDENT  */
    NEWLINE_DEDENT = 271,          /* NEWLINE_DEDENT  */
    ANCHOR = 272,                  /* ANCHOR  */
    ALIAS = 273,                   /* ALIAS  */
    TAG = 274,                     /* TAG  */
    PLAIN_SCALAR = 275,            /* PLAIN_SCALAR  */
    DQUOTE_STRING = 276,           /* DQUOTE_STRING  */
    SQUOTE_STRING = 277,           /* SQUOTE_STRING  */
    LITERAL_CONTENT = 278,         /* LITERAL_CONTENT  */
    LITERAL = 279,                 /* LITERAL  */
    FOLDED = 280,                  /* FOLDED  */
    TAG_DIRECTIVE = 281,           /* TAG_DIRECTIVE  */
    YAML_DIRECTIVE = 282,          /* YAML_DIRECTIVE  */
    LOW_PREC = 283                 /* LOW_PREC  */
  };
  typedef enum yytokentype yytoken_kind_t;
#endif
/* Token kinds.  */
#define YYEMPTY -2
#define YYEOF 0
#define YYerror 256
#define YYUNDEF 257
#define DOC_START 258
#define DOC_END 259
#define LBRACKET 260
#define RBRACKET 261
#define LBRACE 262
#define RBRACE 263
#define COMMA 264
#define SEQ_ENTRY 265
#define MAP_KEY 266
#define COLON 267
#define NEWLINE 268
#define INDENT 269
#define DEDENT 270
#define NEWLINE_DEDENT 271
#define ANCHOR 272
#define ALIAS 273
#define TAG 274
#define PLAIN_SCALAR 275
#define DQUOTE_STRING 276
#define SQUOTE_STRING 277
#define LITERAL_CONTENT 278
#define LITERAL 279
#define FOLDED 280
#define TAG_DIRECTIVE 281
#define YAML_DIRECTIVE 282
#define LOW_PREC 283

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
union YYSTYPE
{
#line 200 "lib/yaml/yaml.y"

    char *str;
    struct Node *node;

#line 384 "y.tab.c"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE yylval;


int yyparse (void);


#endif /* !YY_YY_Y_TAB_H_INCLUDED  */
/* Symbol kind.  */
enum yysymbol_kind_t
{
  YYSYMBOL_YYEMPTY = -2,
  YYSYMBOL_YYEOF = 0,                      /* "end of file"  */
  YYSYMBOL_YYerror = 1,                    /* error  */
  YYSYMBOL_YYUNDEF = 2,                    /* "invalid token"  */
  YYSYMBOL_DOC_START = 3,                  /* DOC_START  */
  YYSYMBOL_DOC_END = 4,                    /* DOC_END  */
  YYSYMBOL_LBRACKET = 5,                   /* LBRACKET  */
  YYSYMBOL_RBRACKET = 6,                   /* RBRACKET  */
  YYSYMBOL_LBRACE = 7,                     /* LBRACE  */
  YYSYMBOL_RBRACE = 8,                     /* RBRACE  */
  YYSYMBOL_COMMA = 9,                      /* COMMA  */
  YYSYMBOL_SEQ_ENTRY = 10,                 /* SEQ_ENTRY  */
  YYSYMBOL_MAP_KEY = 11,                   /* MAP_KEY  */
  YYSYMBOL_COLON = 12,                     /* COLON  */
  YYSYMBOL_NEWLINE = 13,                   /* NEWLINE  */
  YYSYMBOL_INDENT = 14,                    /* INDENT  */
  YYSYMBOL_DEDENT = 15,                    /* DEDENT  */
  YYSYMBOL_NEWLINE_DEDENT = 16,            /* NEWLINE_DEDENT  */
  YYSYMBOL_ANCHOR = 17,                    /* ANCHOR  */
  YYSYMBOL_ALIAS = 18,                     /* ALIAS  */
  YYSYMBOL_TAG = 19,                       /* TAG  */
  YYSYMBOL_PLAIN_SCALAR = 20,              /* PLAIN_SCALAR  */
  YYSYMBOL_DQUOTE_STRING = 21,             /* DQUOTE_STRING  */
  YYSYMBOL_SQUOTE_STRING = 22,             /* SQUOTE_STRING  */
  YYSYMBOL_LITERAL_CONTENT = 23,           /* LITERAL_CONTENT  */
  YYSYMBOL_LITERAL = 24,                   /* LITERAL  */
  YYSYMBOL_FOLDED = 25,                    /* FOLDED  */
  YYSYMBOL_TAG_DIRECTIVE = 26,             /* TAG_DIRECTIVE  */
  YYSYMBOL_YAML_DIRECTIVE = 27,            /* YAML_DIRECTIVE  */
  YYSYMBOL_LOW_PREC = 28,                  /* LOW_PREC  */
  YYSYMBOL_YYACCEPT = 29,                  /* $accept  */
  YYSYMBOL_stream = 30,                    /* stream  */
  YYSYMBOL_document = 31,                  /* document  */
  YYSYMBOL_directives = 32,                /* directives  */
  YYSYMBOL_directive = 33,                 /* directive  */
  YYSYMBOL_directive_args = 34,            /* directive_args  */
  YYSYMBOL_TAG_DIRECTIVE_LINE = 35,        /* TAG_DIRECTIVE_LINE  */
  YYSYMBOL_YAML_DIRECTIVE_LINE = 36,       /* YAML_DIRECTIVE_LINE  */
  YYSYMBOL_opt_newlines = 37,              /* opt_newlines  */
  YYSYMBOL_newlines = 38,                  /* newlines  */
  YYSYMBOL_opt_node = 39,                  /* opt_node  */
  YYSYMBOL_node = 40,                      /* node  */
  YYSYMBOL_content = 41,                   /* content  */
  YYSYMBOL_properties = 42,                /* properties  */
  YYSYMBOL_flow_node = 43,                 /* flow_node  */
  YYSYMBOL_block_node = 44,                /* block_node  */
  YYSYMBOL_merged_plain_scalar = 45,       /* merged_plain_scalar  */
  YYSYMBOL_flow_seq_items = 46,            /* flow_seq_items  */
  YYSYMBOL_flow_seq_item = 47,             /* flow_seq_item  */
  YYSYMBOL_flow_map_entries = 48,          /* flow_map_entries  */
  YYSYMBOL_flow_entry = 49,                /* flow_entry  */
  YYSYMBOL_block_sequence = 50,            /* block_sequence  */
  YYSYMBOL_block_mapping = 51,             /* block_mapping  */
  YYSYMBOL_map_entry = 52,                 /* map_entry  */
  YYSYMBOL_entry_key = 53,                 /* entry_key  */
  YYSYMBOL_entry_value = 54,               /* entry_value  */
  YYSYMBOL_opt_entry_value = 55            /* opt_entry_value  */
};
typedef enum yysymbol_kind_t yysymbol_kind_t;




#ifdef short
# undef short
#endif

/* On compilers that do not define __PTRDIFF_MAX__ etc., make sure
   <limits.h> and (if available) <stdint.h> are included
   so that the code can choose integer types of a good width.  */

#ifndef __PTRDIFF_MAX__
# include <limits.h> /* INFRINGES ON USER NAME SPACE */
# if defined __STDC_VERSION__ && 199901 <= __STDC_VERSION__
#  include <stdint.h> /* INFRINGES ON USER NAME SPACE */
#  define YY_STDINT_H
# endif
#endif

/* Narrow types that promote to a signed type and that can represent a
   signed or unsigned integer of at least N bits.  In tables they can
   save space and decrease cache pressure.  Promoting to a signed type
   helps avoid bugs in integer arithmetic.  */

#ifdef __INT_LEAST8_MAX__
typedef __INT_LEAST8_TYPE__ yytype_int8;
#elif defined YY_STDINT_H
typedef int_least8_t yytype_int8;
#else
typedef signed char yytype_int8;
#endif

#ifdef __INT_LEAST16_MAX__
typedef __INT_LEAST16_TYPE__ yytype_int16;
#elif defined YY_STDINT_H
typedef int_least16_t yytype_int16;
#else
typedef short yytype_int16;
#endif

/* Work around bug in HP-UX 11.23, which defines these macros
   incorrectly for preprocessor constants.  This workaround can likely
   be removed in 2023, as HPE has promised support for HP-UX 11.23
   (aka HP-UX 11i v2) only through the end of 2022; see Table 2 of
   <https://h20195.www2.hpe.com/V2/getpdf.aspx/4AA4-7673ENW.pdf>.  */
#ifdef __hpux
# undef UINT_LEAST8_MAX
# undef UINT_LEAST16_MAX
# define UINT_LEAST8_MAX 255
# define UINT_LEAST16_MAX 65535
#endif

#if defined __UINT_LEAST8_MAX__ && __UINT_LEAST8_MAX__ <= __INT_MAX__
typedef __UINT_LEAST8_TYPE__ yytype_uint8;
#elif (!defined __UINT_LEAST8_MAX__ && defined YY_STDINT_H \
       && UINT_LEAST8_MAX <= INT_MAX)
typedef uint_least8_t yytype_uint8;
#elif !defined __UINT_LEAST8_MAX__ && UCHAR_MAX <= INT_MAX
typedef unsigned char yytype_uint8;
#else
typedef short yytype_uint8;
#endif

#if defined __UINT_LEAST16_MAX__ && __UINT_LEAST16_MAX__ <= __INT_MAX__
typedef __UINT_LEAST16_TYPE__ yytype_uint16;
#elif (!defined __UINT_LEAST16_MAX__ && defined YY_STDINT_H \
       && UINT_LEAST16_MAX <= INT_MAX)
typedef uint_least16_t yytype_uint16;
#elif !defined __UINT_LEAST16_MAX__ && USHRT_MAX <= INT_MAX
typedef unsigned short yytype_uint16;
#else
typedef int yytype_uint16;
#endif

#ifndef YYPTRDIFF_T
# if defined __PTRDIFF_TYPE__ && defined __PTRDIFF_MAX__
#  define YYPTRDIFF_T __PTRDIFF_TYPE__
#  define YYPTRDIFF_MAXIMUM __PTRDIFF_MAX__
# elif defined PTRDIFF_MAX
#  ifndef ptrdiff_t
#   include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  endif
#  define YYPTRDIFF_T ptrdiff_t
#  define YYPTRDIFF_MAXIMUM PTRDIFF_MAX
# else
#  define YYPTRDIFF_T long
#  define YYPTRDIFF_MAXIMUM LONG_MAX
# endif
#endif

#ifndef YYSIZE_T
# ifdef __SIZE_TYPE__
#  define YYSIZE_T __SIZE_TYPE__
# elif defined size_t
#  define YYSIZE_T size_t
# elif defined __STDC_VERSION__ && 199901 <= __STDC_VERSION__
#  include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  define YYSIZE_T size_t
# else
#  define YYSIZE_T unsigned
# endif
#endif

#define YYSIZE_MAXIMUM                                  \
  YY_CAST (YYPTRDIFF_T,                                 \
           (YYPTRDIFF_MAXIMUM < YY_CAST (YYSIZE_T, -1)  \
            ? YYPTRDIFF_MAXIMUM                         \
            : YY_CAST (YYSIZE_T, -1)))

#define YYSIZEOF(X) YY_CAST (YYPTRDIFF_T, sizeof (X))


/* Stored state numbers (used for stacks). */
typedef yytype_int8 yy_state_t;

/* State numbers in computations.  */
typedef int yy_state_fast_t;

#ifndef YY_
# if defined YYENABLE_NLS && YYENABLE_NLS
#  if ENABLE_NLS
#   include <libintl.h> /* INFRINGES ON USER NAME SPACE */
#   define YY_(Msgid) dgettext ("bison-runtime", Msgid)
#  endif
# endif
# ifndef YY_
#  define YY_(Msgid) Msgid
# endif
#endif


#ifndef YY_ATTRIBUTE_PURE
# if defined __GNUC__ && 2 < __GNUC__ + (96 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_PURE __attribute__ ((__pure__))
# else
#  define YY_ATTRIBUTE_PURE
# endif
#endif

#ifndef YY_ATTRIBUTE_UNUSED
# if defined __GNUC__ && 2 < __GNUC__ + (7 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_UNUSED __attribute__ ((__unused__))
# else
#  define YY_ATTRIBUTE_UNUSED
# endif
#endif

/* Suppress unused-variable warnings by "using" E.  */
#if ! defined lint || defined __GNUC__
# define YY_USE(E) ((void) (E))
#else
# define YY_USE(E) /* empty */
#endif

/* Suppress an incorrect diagnostic about yylval being uninitialized.  */
#if defined __GNUC__ && ! defined __ICC && 406 <= __GNUC__ * 100 + __GNUC_MINOR__
# if __GNUC__ * 100 + __GNUC_MINOR__ < 407
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")
# else
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")              \
    _Pragma ("GCC diagnostic ignored \"-Wmaybe-uninitialized\"")
# endif
# define YY_IGNORE_MAYBE_UNINITIALIZED_END      \
    _Pragma ("GCC diagnostic pop")
#else
# define YY_INITIAL_VALUE(Value) Value
#endif
#ifndef YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_END
#endif
#ifndef YY_INITIAL_VALUE
# define YY_INITIAL_VALUE(Value) /* Nothing. */
#endif

#if defined __cplusplus && defined __GNUC__ && ! defined __ICC && 6 <= __GNUC__
# define YY_IGNORE_USELESS_CAST_BEGIN                          \
    _Pragma ("GCC diagnostic push")                            \
    _Pragma ("GCC diagnostic ignored \"-Wuseless-cast\"")
# define YY_IGNORE_USELESS_CAST_END            \
    _Pragma ("GCC diagnostic pop")
#endif
#ifndef YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_END
#endif


#define YY_ASSERT(E) ((void) (0 && (E)))

#if !defined yyoverflow

/* The parser invokes alloca or malloc; define the necessary symbols.  */

# ifdef YYSTACK_USE_ALLOCA
#  if YYSTACK_USE_ALLOCA
#   ifdef __GNUC__
#    define YYSTACK_ALLOC __builtin_alloca
#   elif defined __BUILTIN_VA_ARG_INCR
#    include <alloca.h> /* INFRINGES ON USER NAME SPACE */
#   elif defined _AIX
#    define YYSTACK_ALLOC __alloca
#   elif defined _MSC_VER
#    include <malloc.h> /* INFRINGES ON USER NAME SPACE */
#    define alloca _alloca
#   else
#    define YYSTACK_ALLOC alloca
#    if ! defined _ALLOCA_H && ! defined EXIT_SUCCESS
#     include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
      /* Use EXIT_SUCCESS as a witness for stdlib.h.  */
#     ifndef EXIT_SUCCESS
#      define EXIT_SUCCESS 0
#     endif
#    endif
#   endif
#  endif
# endif

# ifdef YYSTACK_ALLOC
   /* Pacify GCC's 'empty if-body' warning.  */
#  define YYSTACK_FREE(Ptr) do { /* empty */; } while (0)
#  ifndef YYSTACK_ALLOC_MAXIMUM
    /* The OS might guarantee only one guard page at the bottom of the stack,
       and a page size can be as small as 4096 bytes.  So we cannot safely
       invoke alloca (N) if N exceeds 4096.  Use a slightly smaller number
       to allow for a few compiler-allocated temporary stack slots.  */
#   define YYSTACK_ALLOC_MAXIMUM 4032 /* reasonable circa 2006 */
#  endif
# else
#  define YYSTACK_ALLOC YYMALLOC
#  define YYSTACK_FREE YYFREE
#  ifndef YYSTACK_ALLOC_MAXIMUM
#   define YYSTACK_ALLOC_MAXIMUM YYSIZE_MAXIMUM
#  endif
#  if (defined __cplusplus && ! defined EXIT_SUCCESS \
       && ! ((defined YYMALLOC || defined malloc) \
             && (defined YYFREE || defined free)))
#   include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
#   ifndef EXIT_SUCCESS
#    define EXIT_SUCCESS 0
#   endif
#  endif
#  ifndef YYMALLOC
#   define YYMALLOC malloc
#   if ! defined malloc && ! defined EXIT_SUCCESS
void *malloc (YYSIZE_T); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
#  ifndef YYFREE
#   define YYFREE free
#   if ! defined free && ! defined EXIT_SUCCESS
void free (void *); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
# endif
#endif /* !defined yyoverflow */

#if (! defined yyoverflow \
     && (! defined __cplusplus \
         || (defined YYSTYPE_IS_TRIVIAL && YYSTYPE_IS_TRIVIAL)))

/* A type that is properly aligned for any stack member.  */
union yyalloc
{
  yy_state_t yyss_alloc;
  YYSTYPE yyvs_alloc;
};

/* The size of the maximum gap between one aligned stack and the next.  */
# define YYSTACK_GAP_MAXIMUM (YYSIZEOF (union yyalloc) - 1)

/* The size of an array large to enough to hold all stacks, each with
   N elements.  */
# define YYSTACK_BYTES(N) \
     ((N) * (YYSIZEOF (yy_state_t) + YYSIZEOF (YYSTYPE)) \
      + YYSTACK_GAP_MAXIMUM)

# define YYCOPY_NEEDED 1

/* Relocate STACK from its old location to the new one.  The
   local variables YYSIZE and YYSTACKSIZE give the old and new number of
   elements in the stack, and YYPTR gives the new location of the
   stack.  Advance YYPTR to a properly aligned location for the next
   stack.  */
# define YYSTACK_RELOCATE(Stack_alloc, Stack)                           \
    do                                                                  \
      {                                                                 \
        YYPTRDIFF_T yynewbytes;                                         \
        YYCOPY (&yyptr->Stack_alloc, Stack, yysize);                    \
        Stack = &yyptr->Stack_alloc;                                    \
        yynewbytes = yystacksize * YYSIZEOF (*Stack) + YYSTACK_GAP_MAXIMUM; \
        yyptr += yynewbytes / YYSIZEOF (*yyptr);                        \
      }                                                                 \
    while (0)

#endif

#if defined YYCOPY_NEEDED && YYCOPY_NEEDED
/* Copy COUNT objects from SRC to DST.  The source and destination do
   not overlap.  */
# ifndef YYCOPY
#  if defined __GNUC__ && 1 < __GNUC__
#   define YYCOPY(Dst, Src, Count) \
      __builtin_memcpy (Dst, Src, YY_CAST (YYSIZE_T, (Count)) * sizeof (*(Src)))
#  else
#   define YYCOPY(Dst, Src, Count)              \
      do                                        \
        {                                       \
          YYPTRDIFF_T yyi;                      \
          for (yyi = 0; yyi < (Count); yyi++)   \
            (Dst)[yyi] = (Src)[yyi];            \
        }                                       \
      while (0)
#  endif
# endif
#endif /* !YYCOPY_NEEDED */

/* YYFINAL -- State number of the termination state.  */
#define YYFINAL  2
/* YYLAST -- Last index in YYTABLE.  */
#define YYLAST   179

/* YYNTOKENS -- Number of terminals.  */
#define YYNTOKENS  29
/* YYNNTS -- Number of nonterminals.  */
#define YYNNTS  27
/* YYNRULES -- Number of rules.  */
#define YYNRULES  72
/* YYNSTATES -- Number of states.  */
#define YYNSTATES  108

/* YYMAXUTOK -- Last valid token kind.  */
#define YYMAXUTOK   283


/* YYTRANSLATE(TOKEN-NUM) -- Symbol number corresponding to TOKEN-NUM
   as returned by yylex, with out-of-bounds checking.  */
#define YYTRANSLATE(YYX)                                \
  (0 <= (YYX) && (YYX) <= YYMAXUTOK                     \
   ? YY_CAST (yysymbol_kind_t, yytranslate[YYX])        \
   : YYSYMBOL_YYUNDEF)

/* YYTRANSLATE[TOKEN-NUM] -- Symbol number corresponding to TOKEN-NUM
   as returned by yylex.  */
static const yytype_int8 yytranslate[] =
{
       0,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     1,     2,     3,     4,
       5,     6,     7,     8,     9,    10,    11,    12,    13,    14,
      15,    16,    17,    18,    19,    20,    21,    22,    23,    24,
      25,    26,    27,    28
};

#if YYDEBUG
/* YYRLINE[YYN] -- Source line where rule number YYN was defined.  */
static const yytype_int16 yyrline[] =
{
       0,   234,   234,   235,   241,   245,   246,   247,   248,   249,
     253,   254,   258,   259,   263,   264,   268,   272,   276,   277,
     281,   282,   286,   287,   291,   292,   298,   302,   303,   307,
     308,   309,   310,   314,   315,   316,   317,   318,   319,   320,
     321,   325,   326,   327,   328,   332,   333,   337,   338,   339,
     340,   341,   345,   346,   347,   351,   352,   353,   357,   358,
     362,   363,   367,   368,   372,   373,   377,   378,   382,   383,
     384,   388,   389
};
#endif

/** Accessing symbol of state STATE.  */
#define YY_ACCESSING_SYMBOL(State) YY_CAST (yysymbol_kind_t, yystos[State])

#if YYDEBUG || 0
/* The user-facing name of the symbol whose (internal) number is
   YYSYMBOL.  No bounds checking.  */
static const char *yysymbol_name (yysymbol_kind_t yysymbol) YY_ATTRIBUTE_UNUSED;

/* YYTNAME[SYMBOL-NUM] -- String name of the symbol SYMBOL-NUM.
   First, the terminals, then, starting at YYNTOKENS, nonterminals.  */
static const char *const yytname[] =
{
  "\"end of file\"", "error", "\"invalid token\"", "DOC_START", "DOC_END",
  "LBRACKET", "RBRACKET", "LBRACE", "RBRACE", "COMMA", "SEQ_ENTRY",
  "MAP_KEY", "COLON", "NEWLINE", "INDENT", "DEDENT", "NEWLINE_DEDENT",
  "ANCHOR", "ALIAS", "TAG", "PLAIN_SCALAR", "DQUOTE_STRING",
  "SQUOTE_STRING", "LITERAL_CONTENT", "LITERAL", "FOLDED", "TAG_DIRECTIVE",
  "YAML_DIRECTIVE", "LOW_PREC", "$accept", "stream", "document",
  "directives", "directive", "directive_args", "TAG_DIRECTIVE_LINE",
  "YAML_DIRECTIVE_LINE", "opt_newlines", "newlines", "opt_node", "node",
  "content", "properties", "flow_node", "block_node",
  "merged_plain_scalar", "flow_seq_items", "flow_seq_item",
  "flow_map_entries", "flow_entry", "block_sequence", "block_mapping",
  "map_entry", "entry_key", "entry_value", "opt_entry_value", YY_NULLPTR
};

static const char *
yysymbol_name (yysymbol_kind_t yysymbol)
{
  return yytname[yysymbol];
}
#endif

#define YYPACT_NINF (-31)

#define yypact_value_is_default(Yyn) \
  ((Yyn) == YYPACT_NINF)

#define YYTABLE_NINF (-66)

#define yytable_value_is_error(Yyn) \
  0

/* YYPACT[STATE-NUM] -- Index in YYTABLE of the portion describing
   STATE-NUM.  */
static const yytype_int16 yypact[] =
{
     -31,    89,   -31,    -2,   -31,   112,    38,   154,   133,   -31,
      11,   -31,    11,   -31,   -31,   -31,    13,    15,    23,    12,
     -31,     4,   -31,   -31,   -31,    41,   -31,   154,   -31,   -31,
      49,    48,    60,   -31,    41,   -31,   -31,   154,    64,   -31,
     154,    41,    10,   -31,    41,   -31,    41,     9,   -31,    22,
     -31,    41,    37,    11,    61,    65,   -31,   -31,    12,   -31,
       2,    11,   -31,    11,   -31,    41,    72,   -31,    76,   154,
     -31,   -31,   -31,   -31,   -31,    52,   -31,   154,    54,   -31,
     154,   154,   -31,    11,    11,    20,   -31,   -31,   154,     7,
     154,    22,   -31,   -31,    11,   -31,   -31,   -31,   -31,   154,
     -31,   -31,    82,    55,    11,   -31,   -31,   -31
};

/* YYDEFACT[STATE-NUM] -- Default reduction number in state STATE-NUM.
   Performed when YYTABLE does not specify something else to do.  Zero
   means the default is an error.  */
static const yytype_int8 yydefact[] =
{
       2,     0,     1,    18,     8,     0,     0,    23,    23,     4,
      18,    36,    18,    45,    34,    35,     0,     0,     0,     0,
       3,     0,    10,    12,    13,     5,    24,    26,    27,    28,
      33,    41,    42,    62,    72,     9,    20,    23,    19,    40,
      51,    52,     0,    47,    72,    38,    59,     0,    55,    58,
      60,    22,     0,    18,    29,    30,    43,    44,     0,    14,
       0,    18,    11,    18,    64,     0,    25,    46,     0,     0,
      71,    65,     6,    21,    50,    53,    39,    49,    54,    37,
      57,    23,    66,    18,    18,     0,    17,    15,    23,     0,
      23,    63,    48,    56,    18,    31,    32,    16,     7,     0,
      68,    61,     0,    28,    18,    69,    70,    67
};

/* YYPGOTO[NTERM-NUM].  */
static const yytype_int8 yypgoto[] =
{
     -31,   -31,   -31,   -31,    66,    33,   -31,   -31,    -9,    93,
       0,    -1,    77,   -31,    14,     6,   -31,   -31,   -30,   -31,
      32,   -31,   -31,     3,     1,   -21,    80
};

/* YYDEFGOTO[NTERM-NUM].  */
static const yytype_int8 yydefgoto[] =
{
       0,     1,    20,    21,    22,    60,    23,    24,    37,    38,
      50,    51,    26,    27,    28,    29,    30,    42,    43,    47,
      48,    31,    32,    33,    34,    64,    71
};

/* YYTABLE[YYPACT[STATE-NUM]] -- What to do in state STATE-NUM.  If
   positive, shift that token.  If negative, reduce the rule whose
   number is the opposite.  If YYTABLE_NINF, syntax error.  */
static const yytype_int8 yytable[] =
{
      25,    54,    35,    55,    41,    46,    44,    61,    53,    49,
      74,    36,     5,    70,     6,    86,    76,    79,    80,    77,
      75,    99,    87,    70,    36,    11,    65,    13,    14,    15,
      18,    19,    59,    97,   -62,   -62,    56,    72,    57,    41,
      87,    44,    58,     5,    82,     6,    45,    92,     7,     8,
      73,    81,    88,    63,    89,    10,    11,    12,    13,    14,
      15,    68,    16,    17,   -64,   -64,   -65,   -65,    65,    67,
     105,   106,    91,    69,    95,    96,    41,    73,    44,    46,
      83,    94,    84,    49,   -24,   102,    90,    62,    98,     2,
     101,    85,     3,     4,     5,   107,     6,   104,    65,     7,
       8,    52,     9,   100,    66,   103,    10,    11,    12,    13,
      14,    15,    93,    16,    17,    18,    19,     5,    39,     6,
       0,    40,     7,     8,    78,     0,     0,     0,     0,    10,
      11,    12,    13,    14,    15,     0,    16,    17,     5,     0,
       6,     0,     0,     7,     8,     0,    36,     0,     0,     0,
      10,    11,    12,    13,    14,    15,     0,    16,    17,     5,
       0,     6,     0,     0,     7,     8,     0,     0,     0,     0,
       0,    10,    11,    12,    13,    14,    15,     0,    16,    17
};

static const yytype_int8 yycheck[] =
{
       1,    10,     4,    12,     5,     6,     5,     3,     8,     6,
      40,    13,     5,    34,     7,    13,     6,     8,     9,     9,
      41,    14,    20,    44,    13,    18,    27,    20,    21,    22,
      26,    27,    20,    13,    12,    13,    23,    37,    23,    40,
      20,    40,    19,     5,    53,     7,     8,    77,    10,    11,
      13,    14,    61,    12,    63,    17,    18,    19,    20,    21,
      22,    13,    24,    25,    12,    13,    12,    13,    69,    20,
      15,    16,    69,    13,    83,    84,    77,    13,    77,    80,
      19,    81,    17,    80,    12,    94,    10,    21,    88,     0,
      90,    58,     3,     4,     5,   104,     7,    15,    99,    10,
      11,     8,    13,    89,    27,    99,    17,    18,    19,    20,
      21,    22,    80,    24,    25,    26,    27,     5,     6,     7,
      -1,     9,    10,    11,    44,    -1,    -1,    -1,    -1,    17,
      18,    19,    20,    21,    22,    -1,    24,    25,     5,    -1,
       7,    -1,    -1,    10,    11,    -1,    13,    -1,    -1,    -1,
      17,    18,    19,    20,    21,    22,    -1,    24,    25,     5,
      -1,     7,    -1,    -1,    10,    11,    -1,    -1,    -1,    -1,
      -1,    17,    18,    19,    20,    21,    22,    -1,    24,    25
};

/* YYSTOS[STATE-NUM] -- The symbol kind of the accessing symbol of
   state STATE-NUM.  */
static const yytype_int8 yystos[] =
{
       0,    30,     0,     3,     4,     5,     7,    10,    11,    13,
      17,    18,    19,    20,    21,    22,    24,    25,    26,    27,
      31,    32,    33,    35,    36,    40,    41,    42,    43,    44,
      45,    50,    51,    52,    53,     4,    13,    37,    38,     6,
       9,    40,    46,    47,    53,     8,    40,    48,    49,    52,
      39,    40,    38,    39,    37,    37,    23,    23,    19,    20,
      34,     3,    33,    12,    54,    40,    41,    20,    13,    13,
      54,    55,    39,    13,    47,    54,     6,     9,    55,     8,
       9,    14,    37,    19,    17,    34,    13,    20,    37,    37,
      10,    52,    47,    49,    39,    37,    37,    13,    39,    14,
      43,    39,    37,    44,    15,    15,    16,    37
};

/* YYR1[RULE-NUM] -- Symbol kind of the left-hand side of rule RULE-NUM.  */
static const yytype_int8 yyr1[] =
{
       0,    29,    30,    30,    30,    31,    31,    31,    31,    31,
      32,    32,    33,    33,    34,    34,    35,    36,    37,    37,
      38,    38,    39,    39,    40,    40,    40,    41,    41,    42,
      42,    42,    42,    43,    43,    43,    43,    43,    43,    43,
      43,    44,    44,    44,    44,    45,    45,    46,    46,    46,
      46,    46,    47,    47,    47,    48,    48,    48,    49,    49,
      50,    50,    51,    51,    52,    52,    53,    53,    54,    54,
      54,    55,    55
};

/* YYR2[RULE-NUM] -- Number of symbols on the right-hand side of rule RULE-NUM.  */
static const yytype_int8 yyr2[] =
{
       0,     2,     0,     2,     2,     1,     3,     4,     1,     2,
       1,     2,     1,     1,     1,     2,     4,     3,     0,     1,
       1,     2,     1,     0,     1,     2,     1,     1,     1,     2,
       2,     4,     4,     1,     1,     1,     1,     3,     2,     3,
       2,     1,     1,     2,     2,     1,     2,     1,     3,     2,
       2,     1,     1,     2,     2,     1,     3,     2,     1,     1,
       2,     4,     1,     3,     2,     2,     3,     7,     3,     5,
       5,     1,     0
};


enum { YYENOMEM = -2 };

#define yyerrok         (yyerrstatus = 0)
#define yyclearin       (yychar = YYEMPTY)

#define YYACCEPT        goto yyacceptlab
#define YYABORT         goto yyabortlab
#define YYERROR         goto yyerrorlab
#define YYNOMEM         goto yyexhaustedlab


#define YYRECOVERING()  (!!yyerrstatus)

#define YYBACKUP(Token, Value)                                    \
  do                                                              \
    if (yychar == YYEMPTY)                                        \
      {                                                           \
        yychar = (Token);                                         \
        yylval = (Value);                                         \
        YYPOPSTACK (yylen);                                       \
        yystate = *yyssp;                                         \
        goto yybackup;                                            \
      }                                                           \
    else                                                          \
      {                                                           \
        yyerror (YY_("syntax error: cannot back up")); \
        YYERROR;                                                  \
      }                                                           \
  while (0)

/* Backward compatibility with an undocumented macro.
   Use YYerror or YYUNDEF. */
#define YYERRCODE YYUNDEF


/* Enable debugging if requested.  */
#if YYDEBUG

# ifndef YYFPRINTF
#  include <stdio.h> /* INFRINGES ON USER NAME SPACE */
#  define YYFPRINTF fprintf
# endif

# define YYDPRINTF(Args)                        \
do {                                            \
  if (yydebug)                                  \
    YYFPRINTF Args;                             \
} while (0)




# define YY_SYMBOL_PRINT(Title, Kind, Value, Location)                    \
do {                                                                      \
  if (yydebug)                                                            \
    {                                                                     \
      YYFPRINTF (stderr, "%s ", Title);                                   \
      yy_symbol_print (stderr,                                            \
                  Kind, Value); \
      YYFPRINTF (stderr, "\n");                                           \
    }                                                                     \
} while (0)


/*-----------------------------------.
| Print this symbol's value on YYO.  |
`-----------------------------------*/

static void
yy_symbol_value_print (FILE *yyo,
                       yysymbol_kind_t yykind, YYSTYPE const * const yyvaluep)
{
  FILE *yyoutput = yyo;
  YY_USE (yyoutput);
  if (!yyvaluep)
    return;
  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  YY_USE (yykind);
  YY_IGNORE_MAYBE_UNINITIALIZED_END
}


/*---------------------------.
| Print this symbol on YYO.  |
`---------------------------*/

static void
yy_symbol_print (FILE *yyo,
                 yysymbol_kind_t yykind, YYSTYPE const * const yyvaluep)
{
  YYFPRINTF (yyo, "%s %s (",
             yykind < YYNTOKENS ? "token" : "nterm", yysymbol_name (yykind));

  yy_symbol_value_print (yyo, yykind, yyvaluep);
  YYFPRINTF (yyo, ")");
}

/*------------------------------------------------------------------.
| yy_stack_print -- Print the state stack from its BOTTOM up to its |
| TOP (included).                                                   |
`------------------------------------------------------------------*/

static void
yy_stack_print (yy_state_t *yybottom, yy_state_t *yytop)
{
  YYFPRINTF (stderr, "Stack now");
  for (; yybottom <= yytop; yybottom++)
    {
      int yybot = *yybottom;
      YYFPRINTF (stderr, " %d", yybot);
    }
  YYFPRINTF (stderr, "\n");
}

# define YY_STACK_PRINT(Bottom, Top)                            \
do {                                                            \
  if (yydebug)                                                  \
    yy_stack_print ((Bottom), (Top));                           \
} while (0)


/*------------------------------------------------.
| Report that the YYRULE is going to be reduced.  |
`------------------------------------------------*/

static void
yy_reduce_print (yy_state_t *yyssp, YYSTYPE *yyvsp,
                 int yyrule)
{
  int yylno = yyrline[yyrule];
  int yynrhs = yyr2[yyrule];
  int yyi;
  YYFPRINTF (stderr, "Reducing stack by rule %d (line %d):\n",
             yyrule - 1, yylno);
  /* The symbols being reduced.  */
  for (yyi = 0; yyi < yynrhs; yyi++)
    {
      YYFPRINTF (stderr, "   $%d = ", yyi + 1);
      yy_symbol_print (stderr,
                       YY_ACCESSING_SYMBOL (+yyssp[yyi + 1 - yynrhs]),
                       &yyvsp[(yyi + 1) - (yynrhs)]);
      YYFPRINTF (stderr, "\n");
    }
}

# define YY_REDUCE_PRINT(Rule)          \
do {                                    \
  if (yydebug)                          \
    yy_reduce_print (yyssp, yyvsp, Rule); \
} while (0)

/* Nonzero means print parse trace.  It is left uninitialized so that
   multiple parsers can coexist.  */
int yydebug;
#else /* !YYDEBUG */
# define YYDPRINTF(Args) ((void) 0)
# define YY_SYMBOL_PRINT(Title, Kind, Value, Location)
# define YY_STACK_PRINT(Bottom, Top)
# define YY_REDUCE_PRINT(Rule)
#endif /* !YYDEBUG */


/* YYINITDEPTH -- initial size of the parser's stacks.  */
#ifndef YYINITDEPTH
# define YYINITDEPTH 200
#endif

/* YYMAXDEPTH -- maximum size the stacks can grow to (effective only
   if the built-in stack extension method is used).

   Do not make this value too large; the results are undefined if
   YYSTACK_ALLOC_MAXIMUM < YYSTACK_BYTES (YYMAXDEPTH)
   evaluated with infinite-precision integer arithmetic.  */

#ifndef YYMAXDEPTH
# define YYMAXDEPTH 10000
#endif






/*-----------------------------------------------.
| Release the memory associated to this symbol.  |
`-----------------------------------------------*/

static void
yydestruct (const char *yymsg,
            yysymbol_kind_t yykind, YYSTYPE *yyvaluep)
{
  YY_USE (yyvaluep);
  if (!yymsg)
    yymsg = "Deleting";
  YY_SYMBOL_PRINT (yymsg, yykind, yyvaluep, yylocationp);

  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  YY_USE (yykind);
  YY_IGNORE_MAYBE_UNINITIALIZED_END
}


/* Lookahead token kind.  */
int yychar;

/* The semantic value of the lookahead symbol.  */
YYSTYPE yylval;
/* Number of syntax errors so far.  */
int yynerrs;




/*----------.
| yyparse.  |
`----------*/

int
yyparse (void)
{
    yy_state_fast_t yystate = 0;
    /* Number of tokens to shift before error messages enabled.  */
    int yyerrstatus = 0;

    /* Refer to the stacks through separate pointers, to allow yyoverflow
       to reallocate them elsewhere.  */

    /* Their size.  */
    YYPTRDIFF_T yystacksize = YYINITDEPTH;

    /* The state stack: array, bottom, top.  */
    yy_state_t yyssa[YYINITDEPTH];
    yy_state_t *yyss = yyssa;
    yy_state_t *yyssp = yyss;

    /* The semantic value stack: array, bottom, top.  */
    YYSTYPE yyvsa[YYINITDEPTH];
    YYSTYPE *yyvs = yyvsa;
    YYSTYPE *yyvsp = yyvs;

  int yyn;
  /* The return value of yyparse.  */
  int yyresult;
  /* Lookahead symbol kind.  */
  yysymbol_kind_t yytoken = YYSYMBOL_YYEMPTY;
  /* The variables used to return semantic value and location from the
     action routines.  */
  YYSTYPE yyval;



#define YYPOPSTACK(N)   (yyvsp -= (N), yyssp -= (N))

  /* The number of symbols on the RHS of the reduced rule.
     Keep to zero when no symbol should be popped.  */
  int yylen = 0;

  YYDPRINTF ((stderr, "Starting parse\n"));

  yychar = YYEMPTY; /* Cause a token to be read.  */

  goto yysetstate;


/*------------------------------------------------------------.
| yynewstate -- push a new state, which is found in yystate.  |
`------------------------------------------------------------*/
yynewstate:
  /* In all cases, when you get here, the value and location stacks
     have just been pushed.  So pushing a state here evens the stacks.  */
  yyssp++;


/*--------------------------------------------------------------------.
| yysetstate -- set current state (the top of the stack) to yystate.  |
`--------------------------------------------------------------------*/
yysetstate:
  YYDPRINTF ((stderr, "Entering state %d\n", yystate));
  YY_ASSERT (0 <= yystate && yystate < YYNSTATES);
  YY_IGNORE_USELESS_CAST_BEGIN
  *yyssp = YY_CAST (yy_state_t, yystate);
  YY_IGNORE_USELESS_CAST_END
  YY_STACK_PRINT (yyss, yyssp);

  if (yyss + yystacksize - 1 <= yyssp)
#if !defined yyoverflow && !defined YYSTACK_RELOCATE
    YYNOMEM;
#else
    {
      /* Get the current used size of the three stacks, in elements.  */
      YYPTRDIFF_T yysize = yyssp - yyss + 1;

# if defined yyoverflow
      {
        /* Give user a chance to reallocate the stack.  Use copies of
           these so that the &'s don't force the real ones into
           memory.  */
        yy_state_t *yyss1 = yyss;
        YYSTYPE *yyvs1 = yyvs;

        /* Each stack pointer address is followed by the size of the
           data in use in that stack, in bytes.  This used to be a
           conditional around just the two extra args, but that might
           be undefined if yyoverflow is a macro.  */
        yyoverflow (YY_("memory exhausted"),
                    &yyss1, yysize * YYSIZEOF (*yyssp),
                    &yyvs1, yysize * YYSIZEOF (*yyvsp),
                    &yystacksize);
        yyss = yyss1;
        yyvs = yyvs1;
      }
# else /* defined YYSTACK_RELOCATE */
      /* Extend the stack our own way.  */
      if (YYMAXDEPTH <= yystacksize)
        YYNOMEM;
      yystacksize *= 2;
      if (YYMAXDEPTH < yystacksize)
        yystacksize = YYMAXDEPTH;

      {
        yy_state_t *yyss1 = yyss;
        union yyalloc *yyptr =
          YY_CAST (union yyalloc *,
                   YYSTACK_ALLOC (YY_CAST (YYSIZE_T, YYSTACK_BYTES (yystacksize))));
        if (! yyptr)
          YYNOMEM;
        YYSTACK_RELOCATE (yyss_alloc, yyss);
        YYSTACK_RELOCATE (yyvs_alloc, yyvs);
#  undef YYSTACK_RELOCATE
        if (yyss1 != yyssa)
          YYSTACK_FREE (yyss1);
      }
# endif

      yyssp = yyss + yysize - 1;
      yyvsp = yyvs + yysize - 1;

      YY_IGNORE_USELESS_CAST_BEGIN
      YYDPRINTF ((stderr, "Stack size increased to %ld\n",
                  YY_CAST (long, yystacksize)));
      YY_IGNORE_USELESS_CAST_END

      if (yyss + yystacksize - 1 <= yyssp)
        YYABORT;
    }
#endif /* !defined yyoverflow && !defined YYSTACK_RELOCATE */


  if (yystate == YYFINAL)
    YYACCEPT;

  goto yybackup;


/*-----------.
| yybackup.  |
`-----------*/
yybackup:
  /* Do appropriate processing given the current state.  Read a
     lookahead token if we need one and don't already have one.  */

  /* First try to decide what to do without reference to lookahead token.  */
  yyn = yypact[yystate];
  if (yypact_value_is_default (yyn))
    goto yydefault;

  /* Not known => get a lookahead token if don't already have one.  */

  /* YYCHAR is either empty, or end-of-input, or a valid lookahead.  */
  if (yychar == YYEMPTY)
    {
      YYDPRINTF ((stderr, "Reading a token\n"));
      yychar = yylex ();
    }

  if (yychar <= YYEOF)
    {
      yychar = YYEOF;
      yytoken = YYSYMBOL_YYEOF;
      YYDPRINTF ((stderr, "Now at end of input.\n"));
    }
  else if (yychar == YYerror)
    {
      /* The scanner already issued an error message, process directly
         to error recovery.  But do not keep the error token as
         lookahead, it is too special and may lead us to an endless
         loop in error recovery. */
      yychar = YYUNDEF;
      yytoken = YYSYMBOL_YYerror;
      goto yyerrlab1;
    }
  else
    {
      yytoken = YYTRANSLATE (yychar);
      YY_SYMBOL_PRINT ("Next token is", yytoken, &yylval, &yylloc);
    }

  /* If the proper action on seeing token YYTOKEN is to reduce or to
     detect an error, take that action.  */
  yyn += yytoken;
  if (yyn < 0 || YYLAST < yyn || yycheck[yyn] != yytoken)
    goto yydefault;
  yyn = yytable[yyn];
  if (yyn <= 0)
    {
      if (yytable_value_is_error (yyn))
        goto yyerrlab;
      yyn = -yyn;
      goto yyreduce;
    }

  /* Count tokens shifted since error; after three, turn off error
     status.  */
  if (yyerrstatus)
    yyerrstatus--;

  /* Shift the lookahead token.  */
  YY_SYMBOL_PRINT ("Shifting", yytoken, &yylval, &yylloc);
  yystate = yyn;
  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  *++yyvsp = yylval;
  YY_IGNORE_MAYBE_UNINITIALIZED_END

  /* Discard the shifted token.  */
  yychar = YYEMPTY;
  goto yynewstate;


/*-----------------------------------------------------------.
| yydefault -- do the default action for the current state.  |
`-----------------------------------------------------------*/
yydefault:
  yyn = yydefact[yystate];
  if (yyn == 0)
    goto yyerrlab;
  goto yyreduce;


/*-----------------------------.
| yyreduce -- do a reduction.  |
`-----------------------------*/
yyreduce:
  /* yyn is the number of a rule to reduce with.  */
  yylen = yyr2[yyn];

  /* If YYLEN is nonzero, implement the default value of the action:
     '$$ = $1'.

     Otherwise, the following line sets YYVAL to garbage.
     This behavior is undocumented and Bison
     users should not rely upon it.  Assigning to YYVAL
     unconditionally makes the parser a bit smaller, and it avoids a
     GCC warning that YYVAL may be used uninitialized.  */
  yyval = yyvsp[1-yylen];


  YY_REDUCE_PRINT (yyn);
  switch (yyn)
    {
  case 2: /* stream: %empty  */
#line 234 "lib/yaml/yaml.y"
                                    { root = make_stream(NULL); (yyval.node) = root; }
#line 1506 "y.tab.c"
    break;

  case 3: /* stream: stream document  */
#line 235 "lib/yaml/yaml.y"
                                    { 
                                      if ((yyvsp[-1].node)->children) append_node((yyvsp[-1].node)->children, (yyvsp[0].node)); 
                                      else (yyvsp[-1].node)->children = (yyvsp[0].node); 
                                      (yyval.node) = (yyvsp[-1].node); 
                                      root = (yyval.node); 
                                    }
#line 1517 "y.tab.c"
    break;

  case 4: /* stream: stream NEWLINE  */
#line 241 "lib/yaml/yaml.y"
                                    { (yyval.node) = (yyvsp[-1].node); }
#line 1523 "y.tab.c"
    break;

  case 5: /* document: node  */
#line 245 "lib/yaml/yaml.y"
           { (yyval.node) = (yyvsp[0].node); }
#line 1529 "y.tab.c"
    break;

  case 6: /* document: DOC_START opt_newlines opt_node  */
#line 246 "lib/yaml/yaml.y"
                                      { (yyval.node) = (yyvsp[0].node); }
#line 1535 "y.tab.c"
    break;

  case 7: /* document: directives DOC_START opt_newlines opt_node  */
#line 247 "lib/yaml/yaml.y"
                                                 { (yyval.node) = (yyvsp[0].node); }
#line 1541 "y.tab.c"
    break;

  case 8: /* document: DOC_END  */
#line 248 "lib/yaml/yaml.y"
              { (yyval.node) = make_null(); }
#line 1547 "y.tab.c"
    break;

  case 9: /* document: DOC_START DOC_END  */
#line 249 "lib/yaml/yaml.y"
                        { (yyval.node) = make_null(); }
#line 1553 "y.tab.c"
    break;

  case 16: /* TAG_DIRECTIVE_LINE: TAG_DIRECTIVE TAG directive_args NEWLINE  */
#line 268 "lib/yaml/yaml.y"
                                               { /* Handle TAG directive */ }
#line 1559 "y.tab.c"
    break;

  case 17: /* YAML_DIRECTIVE_LINE: YAML_DIRECTIVE directive_args NEWLINE  */
#line 272 "lib/yaml/yaml.y"
                                            { /* Handle YAML directive */ }
#line 1565 "y.tab.c"
    break;

  case 22: /* opt_node: node  */
#line 286 "lib/yaml/yaml.y"
           { (yyval.node) = (yyvsp[0].node); }
#line 1571 "y.tab.c"
    break;

  case 23: /* opt_node: %empty  */
#line 287 "lib/yaml/yaml.y"
                  { (yyval.node) = make_null(); }
#line 1577 "y.tab.c"
    break;

  case 24: /* node: content  */
#line 291 "lib/yaml/yaml.y"
                                        { (yyval.node) = (yyvsp[0].node); }
#line 1583 "y.tab.c"
    break;

  case 25: /* node: properties content  */
#line 292 "lib/yaml/yaml.y"
                                        {
          // Apply properties to content
          (yyval.node) = (yyvsp[0].node);
          if ((yyvsp[-1].node)->anchor) (yyval.node) = make_anchor((yyvsp[-1].node)->anchor, (yyval.node));
          if ((yyvsp[-1].node)->tag)    (yyval.node) = make_tag((yyvsp[-1].node)->tag, (yyval.node));
      }
#line 1594 "y.tab.c"
    break;

  case 26: /* node: properties  */
#line 298 "lib/yaml/yaml.y"
                                        { (yyval.node) = (yyvsp[0].node); }
#line 1600 "y.tab.c"
    break;

  case 29: /* properties: ANCHOR opt_newlines  */
#line 307 "lib/yaml/yaml.y"
                                        { (yyval.node) = make_anchor((yyvsp[-1].str), make_null()); }
#line 1606 "y.tab.c"
    break;

  case 30: /* properties: TAG opt_newlines  */
#line 308 "lib/yaml/yaml.y"
                                        { (yyval.node) = make_tag((yyvsp[-1].str), make_null()); }
#line 1612 "y.tab.c"
    break;

  case 31: /* properties: ANCHOR opt_newlines TAG opt_newlines  */
#line 309 "lib/yaml/yaml.y"
                                            { (yyval.node) = make_anchor((yyvsp[-3].str), make_tag((yyvsp[-1].str), make_null())); }
#line 1618 "y.tab.c"
    break;

  case 32: /* properties: TAG opt_newlines ANCHOR opt_newlines  */
#line 310 "lib/yaml/yaml.y"
                                            { (yyval.node) = make_tag((yyvsp[-3].str), make_anchor((yyvsp[-1].str), make_null())); }
#line 1624 "y.tab.c"
    break;

  case 33: /* flow_node: merged_plain_scalar  */
#line 314 "lib/yaml/yaml.y"
                            { (yyval.node) = make_scalar((yyvsp[0].str)); }
#line 1630 "y.tab.c"
    break;

  case 34: /* flow_node: DQUOTE_STRING  */
#line 315 "lib/yaml/yaml.y"
                            { (yyval.node) = make_scalar((yyvsp[0].str)); }
#line 1636 "y.tab.c"
    break;

  case 35: /* flow_node: SQUOTE_STRING  */
#line 316 "lib/yaml/yaml.y"
                            { (yyval.node) = make_scalar((yyvsp[0].str)); }
#line 1642 "y.tab.c"
    break;

  case 36: /* flow_node: ALIAS  */
#line 317 "lib/yaml/yaml.y"
                            { (yyval.node) = make_alias((yyvsp[0].str)); }
#line 1648 "y.tab.c"
    break;

  case 37: /* flow_node: LBRACE flow_map_entries RBRACE  */
#line 318 "lib/yaml/yaml.y"
                                       { (yyval.node) = make_map((yyvsp[-1].node)); }
#line 1654 "y.tab.c"
    break;

  case 38: /* flow_node: LBRACE RBRACE  */
#line 319 "lib/yaml/yaml.y"
                    { (yyval.node) = make_map(NULL); }
#line 1660 "y.tab.c"
    break;

  case 39: /* flow_node: LBRACKET flow_seq_items RBRACKET  */
#line 320 "lib/yaml/yaml.y"
                                       { (yyval.node) = make_seq((yyvsp[-1].node)); }
#line 1666 "y.tab.c"
    break;

  case 40: /* flow_node: LBRACKET RBRACKET  */
#line 321 "lib/yaml/yaml.y"
                        { (yyval.node) = make_seq(NULL); }
#line 1672 "y.tab.c"
    break;

  case 41: /* block_node: block_sequence  */
#line 325 "lib/yaml/yaml.y"
                     { (yyval.node) = (yyvsp[0].node); }
#line 1678 "y.tab.c"
    break;

  case 42: /* block_node: block_mapping  */
#line 326 "lib/yaml/yaml.y"
                     { (yyval.node) = (yyvsp[0].node); }
#line 1684 "y.tab.c"
    break;

  case 43: /* block_node: LITERAL LITERAL_CONTENT  */
#line 327 "lib/yaml/yaml.y"
                              { (yyval.node) = make_block_scalar((yyvsp[0].str), 0); }
#line 1690 "y.tab.c"
    break;

  case 44: /* block_node: FOLDED LITERAL_CONTENT  */
#line 328 "lib/yaml/yaml.y"
                              { (yyval.node) = make_block_scalar((yyvsp[0].str), 1); }
#line 1696 "y.tab.c"
    break;

  case 45: /* merged_plain_scalar: PLAIN_SCALAR  */
#line 332 "lib/yaml/yaml.y"
                   { (yyval.str) = (yyvsp[0].str); }
#line 1702 "y.tab.c"
    break;

  case 46: /* merged_plain_scalar: merged_plain_scalar PLAIN_SCALAR  */
#line 333 "lib/yaml/yaml.y"
                                       { (yyval.str) = join_scalar_values((yyvsp[-1].str), (yyvsp[0].str)); }
#line 1708 "y.tab.c"
    break;

  case 47: /* flow_seq_items: flow_seq_item  */
#line 337 "lib/yaml/yaml.y"
                                            { (yyval.node) = (yyvsp[0].node); }
#line 1714 "y.tab.c"
    break;

  case 48: /* flow_seq_items: flow_seq_items COMMA flow_seq_item  */
#line 338 "lib/yaml/yaml.y"
                                            { (yyval.node) = append_node((yyvsp[-2].node), (yyvsp[0].node)); }
#line 1720 "y.tab.c"
    break;

  case 49: /* flow_seq_items: flow_seq_items COMMA  */
#line 339 "lib/yaml/yaml.y"
                                            { (yyval.node) = append_node((yyvsp[-1].node), make_null()); }
#line 1726 "y.tab.c"
    break;

  case 50: /* flow_seq_items: COMMA flow_seq_item  */
#line 340 "lib/yaml/yaml.y"
                                            { (yyval.node) = append_node(make_seq(make_null())->children, (yyvsp[0].node)); }
#line 1732 "y.tab.c"
    break;

  case 51: /* flow_seq_items: COMMA  */
#line 341 "lib/yaml/yaml.y"
                                            { (yyval.node) = append_node(make_seq(make_null())->children, make_null()); }
#line 1738 "y.tab.c"
    break;

  case 52: /* flow_seq_item: node  */
#line 345 "lib/yaml/yaml.y"
                                   { (yyval.node) = (yyvsp[0].node); }
#line 1744 "y.tab.c"
    break;

  case 53: /* flow_seq_item: node entry_value  */
#line 346 "lib/yaml/yaml.y"
                                   { (yyval.node) = make_map(append_node((yyvsp[-1].node), (yyvsp[0].node))); }
#line 1750 "y.tab.c"
    break;

  case 54: /* flow_seq_item: entry_key opt_entry_value  */
#line 347 "lib/yaml/yaml.y"
                                   { (yyval.node) = make_map(append_node((yyvsp[-1].node), (yyvsp[0].node))); }
#line 1756 "y.tab.c"
    break;

  case 56: /* flow_map_entries: flow_map_entries COMMA flow_entry  */
#line 352 "lib/yaml/yaml.y"
                                        { (yyval.node) = append_node((yyvsp[-2].node), (yyvsp[0].node)); }
#line 1762 "y.tab.c"
    break;

  case 57: /* flow_map_entries: flow_map_entries COMMA  */
#line 353 "lib/yaml/yaml.y"
                                        { (yyval.node) = (yyvsp[-1].node); }
#line 1768 "y.tab.c"
    break;

  case 59: /* flow_entry: node  */
#line 358 "lib/yaml/yaml.y"
           { (yyval.node) = append_node((yyvsp[0].node), make_null()); }
#line 1774 "y.tab.c"
    break;

  case 60: /* block_sequence: SEQ_ENTRY opt_node  */
#line 362 "lib/yaml/yaml.y"
                         { (yyval.node) = make_seq((yyvsp[0].node)); }
#line 1780 "y.tab.c"
    break;

  case 61: /* block_sequence: block_sequence NEWLINE SEQ_ENTRY opt_node  */
#line 363 "lib/yaml/yaml.y"
                                                { append_node((yyvsp[-3].node)->children, (yyvsp[0].node)); (yyval.node) = (yyvsp[-3].node); }
#line 1786 "y.tab.c"
    break;

  case 62: /* block_mapping: map_entry  */
#line 367 "lib/yaml/yaml.y"
                { (yyval.node) = make_map((yyvsp[0].node)); }
#line 1792 "y.tab.c"
    break;

  case 63: /* block_mapping: block_mapping NEWLINE map_entry  */
#line 368 "lib/yaml/yaml.y"
                                      { append_node((yyvsp[-2].node)->children, (yyvsp[0].node)); (yyval.node) = (yyvsp[-2].node); }
#line 1798 "y.tab.c"
    break;

  case 64: /* map_entry: node entry_value  */
#line 372 "lib/yaml/yaml.y"
                                  { (yyval.node) = append_node((yyvsp[-1].node), (yyvsp[0].node)); }
#line 1804 "y.tab.c"
    break;

  case 65: /* map_entry: entry_key opt_entry_value  */
#line 373 "lib/yaml/yaml.y"
                                  { (yyval.node) = append_node((yyvsp[-1].node), (yyvsp[0].node)); }
#line 1810 "y.tab.c"
    break;

  case 66: /* entry_key: MAP_KEY opt_node opt_newlines  */
#line 377 "lib/yaml/yaml.y"
                                    { (yyval.node) = (yyvsp[-1].node); }
#line 1816 "y.tab.c"
    break;

  case 67: /* entry_key: MAP_KEY newlines INDENT opt_node opt_newlines DEDENT opt_newlines  */
#line 378 "lib/yaml/yaml.y"
                                                                        { (yyval.node) = (yyvsp[-3].node); }
#line 1822 "y.tab.c"
    break;

  case 68: /* entry_value: COLON opt_newlines flow_node  */
#line 382 "lib/yaml/yaml.y"
                                   { (yyval.node) = (yyvsp[0].node); }
#line 1828 "y.tab.c"
    break;

  case 69: /* entry_value: COLON opt_newlines INDENT block_node DEDENT  */
#line 383 "lib/yaml/yaml.y"
                                                  { (yyval.node) = (yyvsp[-1].node); }
#line 1834 "y.tab.c"
    break;

  case 70: /* entry_value: COLON opt_newlines INDENT block_node NEWLINE_DEDENT  */
#line 384 "lib/yaml/yaml.y"
                                                          { (yyval.node) = (yyvsp[-1].node); }
#line 1840 "y.tab.c"
    break;

  case 72: /* opt_entry_value: %empty  */
#line 389 "lib/yaml/yaml.y"
                  { (yyval.node) = make_null(); }
#line 1846 "y.tab.c"
    break;


#line 1850 "y.tab.c"

      default: break;
    }
  /* User semantic actions sometimes alter yychar, and that requires
     that yytoken be updated with the new translation.  We take the
     approach of translating immediately before every use of yytoken.
     One alternative is translating here after every semantic action,
     but that translation would be missed if the semantic action invokes
     YYABORT, YYACCEPT, or YYERROR immediately after altering yychar or
     if it invokes YYBACKUP.  In the case of YYABORT or YYACCEPT, an
     incorrect destructor might then be invoked immediately.  In the
     case of YYERROR or YYBACKUP, subsequent parser actions might lead
     to an incorrect destructor call or verbose syntax error message
     before the lookahead is translated.  */
  YY_SYMBOL_PRINT ("-> $$ =", YY_CAST (yysymbol_kind_t, yyr1[yyn]), &yyval, &yyloc);

  YYPOPSTACK (yylen);
  yylen = 0;

  *++yyvsp = yyval;

  /* Now 'shift' the result of the reduction.  Determine what state
     that goes to, based on the state we popped back to and the rule
     number reduced by.  */
  {
    const int yylhs = yyr1[yyn] - YYNTOKENS;
    const int yyi = yypgoto[yylhs] + *yyssp;
    yystate = (0 <= yyi && yyi <= YYLAST && yycheck[yyi] == *yyssp
               ? yytable[yyi]
               : yydefgoto[yylhs]);
  }

  goto yynewstate;


/*--------------------------------------.
| yyerrlab -- here on detecting error.  |
`--------------------------------------*/
yyerrlab:
  /* Make sure we have latest lookahead translation.  See comments at
     user semantic actions for why this is necessary.  */
  yytoken = yychar == YYEMPTY ? YYSYMBOL_YYEMPTY : YYTRANSLATE (yychar);
  /* If not already recovering from an error, report this error.  */
  if (!yyerrstatus)
    {
      ++yynerrs;
      yyerror (YY_("syntax error"));
    }

  if (yyerrstatus == 3)
    {
      /* If just tried and failed to reuse lookahead token after an
         error, discard it.  */

      if (yychar <= YYEOF)
        {
          /* Return failure if at end of input.  */
          if (yychar == YYEOF)
            YYABORT;
        }
      else
        {
          yydestruct ("Error: discarding",
                      yytoken, &yylval);
          yychar = YYEMPTY;
        }
    }

  /* Else will try to reuse lookahead token after shifting the error
     token.  */
  goto yyerrlab1;


/*---------------------------------------------------.
| yyerrorlab -- error raised explicitly by YYERROR.  |
`---------------------------------------------------*/
yyerrorlab:
  /* Pacify compilers when the user code never invokes YYERROR and the
     label yyerrorlab therefore never appears in user code.  */
  if (0)
    YYERROR;
  ++yynerrs;

  /* Do not reclaim the symbols of the rule whose action triggered
     this YYERROR.  */
  YYPOPSTACK (yylen);
  yylen = 0;
  YY_STACK_PRINT (yyss, yyssp);
  yystate = *yyssp;
  goto yyerrlab1;


/*-------------------------------------------------------------.
| yyerrlab1 -- common code for both syntax error and YYERROR.  |
`-------------------------------------------------------------*/
yyerrlab1:
  yyerrstatus = 3;      /* Each real token shifted decrements this.  */

  /* Pop stack until we find a state that shifts the error token.  */
  for (;;)
    {
      yyn = yypact[yystate];
      if (!yypact_value_is_default (yyn))
        {
          yyn += YYSYMBOL_YYerror;
          if (0 <= yyn && yyn <= YYLAST && yycheck[yyn] == YYSYMBOL_YYerror)
            {
              yyn = yytable[yyn];
              if (0 < yyn)
                break;
            }
        }

      /* Pop the current state because it cannot handle the error token.  */
      if (yyssp == yyss)
        YYABORT;


      yydestruct ("Error: popping",
                  YY_ACCESSING_SYMBOL (yystate), yyvsp);
      YYPOPSTACK (1);
      yystate = *yyssp;
      YY_STACK_PRINT (yyss, yyssp);
    }

  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  *++yyvsp = yylval;
  YY_IGNORE_MAYBE_UNINITIALIZED_END


  /* Shift the error token.  */
  YY_SYMBOL_PRINT ("Shifting", YY_ACCESSING_SYMBOL (yyn), yyvsp, yylsp);

  yystate = yyn;
  goto yynewstate;


/*-------------------------------------.
| yyacceptlab -- YYACCEPT comes here.  |
`-------------------------------------*/
yyacceptlab:
  yyresult = 0;
  goto yyreturnlab;


/*-----------------------------------.
| yyabortlab -- YYABORT comes here.  |
`-----------------------------------*/
yyabortlab:
  yyresult = 1;
  goto yyreturnlab;


/*-----------------------------------------------------------.
| yyexhaustedlab -- YYNOMEM (memory exhaustion) comes here.  |
`-----------------------------------------------------------*/
yyexhaustedlab:
  yyerror (YY_("memory exhausted"));
  yyresult = 2;
  goto yyreturnlab;


/*----------------------------------------------------------.
| yyreturnlab -- parsing is finished, clean up and return.  |
`----------------------------------------------------------*/
yyreturnlab:
  if (yychar != YYEMPTY)
    {
      /* Make sure we have latest lookahead translation.  See comments at
         user semantic actions for why this is necessary.  */
      yytoken = YYTRANSLATE (yychar);
      yydestruct ("Cleanup: discarding lookahead",
                  yytoken, &yylval);
    }
  /* Do not reclaim the symbols of the rule whose action triggered
     this YYABORT or YYACCEPT.  */
  YYPOPSTACK (yylen);
  YY_STACK_PRINT (yyss, yyssp);
  while (yyssp != yyss)
    {
      yydestruct ("Cleanup: popping",
                  YY_ACCESSING_SYMBOL (+*yyssp), yyvsp);
      YYPOPSTACK (1);
    }
#ifndef yyoverflow
  if (yyss != yyssa)
    YYSTACK_FREE (yyss);
#endif

  return yyresult;
}

#line 392 "lib/yaml/yaml.y"


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
