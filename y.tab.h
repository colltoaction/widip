/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison interface for Yacc-like parsers in C

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

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

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

#line 128 "y.tab.h"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE yylval;


int yyparse (void);


#endif /* !YY_YY_Y_TAB_H_INCLUDED  */
