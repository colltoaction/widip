#!/bin/sh
# This script sets up a minimal titi environment by installing a bootstrap parser.

set -e

echo "# Bootstrapping titi..."
mkdir -p bootstrap/src bootstrap/bin

# 1. Create prompt file if missing
if [ ! -f prompt ]; then
    echo "# Creating prompt file..."
    cat <<YAMLEOF > prompt
%YAML 1.2.2
--- !titi
name: titi
version: 1.5.2026
description: "Categorical YAML Computer - Bootstrap Configuration"
YAMLEOF
fi

# 2. Determine bootstrap method
if command -v cc >/dev/null 2>&1; then
    echo "# Found C compiler. attempting C bootstrap..."

    # Extract C sources
    cat <<'CEOF' > bootstrap/src/titi.h
#ifndef TITI_H
#define TITI_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct Node {
    enum { N_SCALAR, N_SEQ, N_MAP, N_ALIAS, N_STREAM, N_NULL, N_DOC } type;
    char *tag, *anchor, *value, *header;
    struct Node *children, *next;
} Node;
extern Node *root;
Node* nnew(int type);
Node* nscalar(char *v);
Node* nseq(Node *c);
Node* nmap(Node *c);
Node* nalias(char *v);
Node* nnull();
Node* ndoc(Node *n, char *h);
Node* napply(Node *n, Node *p);
Node* nappend(Node *l, Node *i);
void p_scalar(char *s);
void nyaml(Node *n, int d, int is_val);
char* jscalar(char *s1, char *s2);
char* nlscalar(char *s1, char *s2);
char* load_prompt_file(const char *filename);
#endif
CEOF

    cat <<'CEOF' > bootstrap/src/titi.c
#include "titi.h"
Node* nnew(int type) { Node *n = calloc(1, sizeof(Node)); n->type = type; return n; }
Node* nscalar(char *v) { Node *n = nnew(N_SCALAR); n->value = v; return n; }
Node* nseq(Node *c) { Node *n = nnew(N_SEQ); n->children = c; return n; }
Node* nmap(Node *c) { Node *n = nnew(N_MAP); n->children = c; return n; }
Node* nalias(char *v) { Node *n = nnew(N_ALIAS); n->value = v; return n; }
Node* nnull() { Node *n = nnew(N_NULL); n->value = strdup("null"); return n; }
Node* ndoc(Node *n, char *h) { Node *d = nnew(N_DOC); d->children = n; d->header = h; return d; }
Node* napply(Node *n, Node *p) { if (!n) n = nnull(); if (p) { n->anchor = p->anchor; n->tag = p->tag; free(p); } return n; }
Node* nappend(Node *l, Node *i) { if (!l) return i; Node *c = l; while (c->next) c = c->next; c->next = i; return l; }
void p_scalar(char *s) {
    if (!s) { printf("null"); return; }
    int quote = 0;
    if (strpbrk(s, ":#[]{}&*!|>-") || strchr(s, ' ')) quote = 1;
    if (quote) putchar('"');
    for (char *c = s; *c; c++) {
        if (*c == '"') printf("\\\""); else if (*c == '\\') printf("\\\\"); else putchar(*c);
    }
    if (quote) putchar('"');
}
void nyaml(Node *n, int d, int is_val) {
    if (!n) return;
    if (n->type == N_STREAM) { for (Node *c = n->children; c; c = c->next) nyaml(c, 0, 0); return; }
    if (n->type == N_DOC) {
        if (n->header) {
            char *h = strdup(n->header); char *p = strstr(h, "---");
            if (p && n->children && (n->children->tag || n->children->anchor)) {
                char *after = p + 3; *after = '\0'; printf("%s", h);
                if (n->children->tag) { printf(" !%s", n->children->tag); n->children->tag = NULL; }
                if (n->children->anchor) { printf(" &%s", n->children->anchor); n->children->anchor = NULL; }
                printf("%s", after); if (*after == '\0' && *(after-1) != '\n') putchar('\n');
            } else printf("%s", n->header);
            free(h);
        } else {
            printf("---");
            if (n->children && n->children->tag) { printf(" !%s", n->children->tag); n->children->tag = NULL; }
            if (n->children && n->children->anchor) { printf(" &%s", n->children->anchor); n->children->anchor = NULL; }
            printf("\n");
        }
        nyaml(n->children, 0, 0); return;
    }
    if (n->type == N_SEQ || n->type == N_MAP) {
        if (is_val) printf("\n");
        if (n->anchor) { for (int i=0; i<d*2; i++) putchar(' '); printf("&%s\n", n->anchor); }
        if (n->tag) { for (int i=0; i<d*2; i++) putchar(' '); printf("!%s\n", n->tag); }
        for (Node *c = n->children; c; ) {
            if (n->type == N_SEQ) { for (int i=0; i<d*2; i++) putchar(' '); printf("- "); nyaml(c, d+1, 1); c = c->next; }
            else {
                Node *key = c; Node *val = c->next; if (!val) break;
                for (int i=0; i<d*2; i++) putchar(' ');
                if (key->anchor) printf("&%s ", key->anchor); if (key->tag) printf("!%s ", key->tag);
                p_scalar(key->value); printf(": "); nyaml(val, d+1, 1); c = val->next;
            }
        }
    } else {
        if (n->anchor) printf("&%s ", n->anchor); if (n->tag) printf("!%s ", n->tag);
        if (n->type == N_SCALAR) { p_scalar(n->value); putchar('\n'); }
        else if (n->type == N_NULL) printf("null\n");
        else if (n->type == N_ALIAS) printf("*%s\n", n->value);
    }
}
char* jscalar(char *s1, char *s2) { char *r = malloc(strlen(s1)+strlen(s2)+2); sprintf(r, "%s %s", s1, s2); free(s1); free(s2); return r; }
char* nlscalar(char *s1, char *s2) { char *r = malloc(strlen(s1)+strlen(s2)+2); sprintf(r, "%s\n%s", s1, s2); free(s1); free(s2); return r; }
char* load_prompt_file(const char *filename) { FILE *f = fopen(filename, "r"); if (!f) return NULL; fseek(f, 0, SEEK_END); long size = ftell(f); fseek(f, 0, SEEK_SET); char *c = malloc(size + 1); if (!c) { fclose(f); return NULL; } fread(c, 1, size, f); c[size] = '\0'; fclose(f); return c; }
CEOF

    cat <<'CEOF' > bootstrap/src/boot.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include "titi.h"
#define BUF_SIZE 65536
char buffer[BUF_SIZE];
Node *current_doc = NULL;
char *trim(char *str) {
    char *end; while(isspace((unsigned char)*str)) str++; if(*str == 0) return str;
    end = str + strlen(str) - 1; while(end > str && isspace((unsigned char)*end)) end--; *(end+1) = 0; return str;
}
char *unquote(char *str) {
    if ((str[0] == '"' && str[strlen(str)-1] == '"') || (str[0] == '\'' && str[strlen(str)-1] == '\'')) {
        str[strlen(str)-1] = 0; return str + 1;
    } return str;
}
Node *parse_flow_seq(char *val) {
    if (val[0] == '[') val++; if (val[strlen(val)-1] == ']') val[strlen(val)-1] = 0;
    Node *seq = nseq(NULL); char *token = strtok(val, ",");
    while(token) {
        char *item = trim(token);
        if(strlen(item) > 0) { Node *s = nscalar(strdup(item)); if (!seq->children) seq->children = s; else nappend(seq->children, s); }
        token = strtok(NULL, ",");
    } return seq;
}
Node *parse_flow_map(char *val) {
    if (val[0] == '{') val++; if (val[strlen(val)-1] == '}') val[strlen(val)-1] = 0;
    Node *map = nmap(NULL); char *token = strtok(val, ",");
    while(token) {
        char *item = trim(token); char *p = strchr(item, ':');
        if (p) {
            *p = 0; char *k = trim(item); char *v = trim(p+1);
            Node *key = nscalar(strdup(k)); Node *val = nscalar(strdup(v)); key->next = val;
            if (!map->children) map->children = key; else nappend(map->children, key);
        } token = strtok(NULL, ",");
    } return map;
}

int main(int argc, char **argv) {
    int boot = 0; int sock_mode = 0; int connect_mode = 0; char *host = NULL; int port = 0;
    if (argc > 1) {
        if (strcmp(argv[1], "--boot") == 0 || strcmp(argv[1], "--idempotent") == 0) boot = 1;
        if (strcmp(argv[1], "--socket") == 0) sock_mode = 1;
        if (strcmp(argv[1], "--connect") == 0 && argc > 3) { connect_mode = 1; host = argv[2]; port = atoi(argv[3]); }
    }

    if (connect_mode) {
        int sock; struct sockaddr_in serv_addr; struct hostent *server;
        sock = socket(AF_INET, SOCK_STREAM, 0); if (sock < 0) exit(1);
        server = gethostbyname(host); if (!server) exit(1);
        bzero((char *) &serv_addr, sizeof(serv_addr)); serv_addr.sin_family = AF_INET;
        bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);
        serv_addr.sin_port = htons(port);
        if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) exit(1);
        
        // Simple select loop for bidirectional cat
        fd_set fds;
        while(1) {
            FD_ZERO(&fds); FD_SET(0, &fds); FD_SET(sock, &fds);
            if (select(sock+1, &fds, NULL, NULL, NULL) < 0) break;
            if (FD_ISSET(0, &fds)) {
                int n = read(0, buffer, BUF_SIZE); if (n <= 0) break;
                write(sock, buffer, n);
            }
            if (FD_ISSET(sock, &fds)) {
                int n = read(sock, buffer, BUF_SIZE); if (n <= 0) break;
                write(1, buffer, n);
            }
        }
        close(sock); return 0;
    }

    if (sock_mode) {
        int server_fd, new_socket; struct sockaddr_in address; int opt = 1; int addrlen = sizeof(address);
        if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) exit(1);
        setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        address.sin_family = AF_INET; address.sin_addr.s_addr = INADDR_ANY; address.sin_port = htons(8080);
        if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) exit(1);
        if (listen(server_fd, 3) < 0) exit(1);
        fcntl(server_fd, F_SETFL, O_NONBLOCK); // 2.10.7 Socket I/O Mode
        printf("# titi socket io mode on 8080\n");
        while(1) {
            new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen);
            if (new_socket >= 0) {
                 if (fork() == 0) {
                    close(server_fd);
                    dup2(new_socket, 0); dup2(new_socket, 1);
                    // Reset args and proceed to parse
                    sock_mode = 0; boot = 0; connect_mode = 0;
                 } else {
                    close(new_socket);
                    continue; // Main loop continues
                 }
            } else {
                usleep(100000); // minimal spin for O_NONBLOCK accept
                continue;
            }
            break; // Child process breaks to parser logic
        }
    }

    FILE *in = stdin; if (boot) { in = fopen("prompt", "r"); if (!in) return 1; }
    size_t len = fread(buffer, 1, BUF_SIZE - 1, in); buffer[len] = 0; if (in != stdin) fclose(in);
    char *line = strtok(buffer, "\n"); int in_block = 0; char *block_key = NULL; char *block_val = NULL; int block_indent = -1;
    Node *stream = nnew(N_STREAM); current_doc = NULL;
    int saw_directive = 0;
    while (line) {
        int indent = 0; char *p = line; while (*p == ' ') { indent++; p++; }
        char *content = trim(line);
        if (in_block) {
            if (strlen(content) == 0) { } else {
                if (block_indent == -1) block_indent = indent;
                if (indent < block_indent) {
                    Node *k = nscalar(strdup(block_key)); Node *v = nscalar(strdup(block_val ? block_val : "")); k->next = v;
                    if (!current_doc->children) current_doc->children = k; else nappend(current_doc->children, k);
                    in_block = 0; block_key = NULL; block_val = NULL; block_indent = -1;
                } else {
                    char *text = line + block_indent; size_t new_len = (block_val ? strlen(block_val) : 0) + strlen(text) + 2;
                    char *new_val = malloc(new_len);
                    if (block_val) { sprintf(new_val, "%s\n%s", block_val, text); free(block_val); } else strcpy(new_val, text);
                    block_val = new_val; line = strtok(NULL, "\n"); continue;
                }
            }
        }
        if (strlen(content) == 0 || content[0] == '#') { line = strtok(NULL, "\n"); continue; }
        if (strncmp(content, "%YAML", 5) == 0) { saw_directive = 1; line = strtok(NULL, "\n"); continue; }
        if (strncmp(content, "---", 3) == 0) {
            if (current_doc) { if (!stream->children) stream->children = current_doc; else nappend(stream->children, current_doc); }
            char *tag = NULL; char *rest = trim(content + 3); if (rest[0] == '!') tag = strdup(rest + 1);
            current_doc = nnew(N_DOC); current_doc->header = strdup(content);
            Node *map = nmap(NULL); if (tag) map->tag = tag; current_doc->children = map;
            line = strtok(NULL, "\n"); continue;
        }
        if (!current_doc) { current_doc = nnew(N_DOC); current_doc->children = nmap(NULL); }
        if (content[0] == '{' && content[strlen(content)-1] == '}') { current_doc->children = parse_flow_map(content); line = strtok(NULL, "\n"); continue; }
        if (content[0] == '[' && content[strlen(content)-1] == ']') { current_doc->children = parse_flow_seq(content); line = strtok(NULL, "\n"); continue; }
        char *pp = strchr(content, ':');
        if (pp) {
            *pp = 0; char *key_str = trim(content); char *val_str = trim(pp+1); key_str = unquote(key_str);
            if (strcmp(val_str, "|") == 0) { in_block = 1; block_key = strdup(key_str); block_val = NULL; block_indent = -1; line = strtok(NULL, "\n"); continue; }
            Node *val_node = NULL;
            if (val_str[0] == '[' && val_str[strlen(val_str)-1] == ']') val_node = parse_flow_seq(val_str);
            else if (val_str[0] == '{' && val_str[strlen(val_str)-1] == '}') val_node = parse_flow_map(val_str);
            else { val_str = unquote(val_str); val_node = nscalar(strdup(val_str)); }
            Node *key_node = nscalar(strdup(key_str)); key_node->next = val_node;
            if (current_doc->children) { if (!current_doc->children->children) current_doc->children->children = key_node; else nappend(current_doc->children->children, key_node); }
        }
        line = strtok(NULL, "\n");
    }
    if (in_block && block_key) {
        Node *k = nscalar(strdup(block_key)); Node *v = nscalar(strdup(block_val ? block_val : "")); k->next = v;
        if (current_doc->children) { if (!current_doc->children->children) current_doc->children->children = k; else nappend(current_doc->children->children, k); }
    }
    if (current_doc) { if (!stream->children) stream->children = current_doc; else nappend(stream->children, current_doc); }
    if (saw_directive || boot) printf("%%YAML 1.2.2\n");
    nyaml(stream, 0, 0); return 0;
}
CEOF

    cc bootstrap/src/boot.c bootstrap/src/titi.c -o bootstrap/bin/titi
    echo "# C bootstrap successful."

elif command -v python3 >/dev/null 2>&1; then
    echo "# C compiler not found. attempting Python bootstrap..."

cat <<'PYTHONEOF' > bootstrap/bin/titi
#!/usr/bin/env python3
import sys
import argparse
class SimpleYAML:
    def __init__(self):
        self.docs = []; self.cur_doc = None; self.in_block = False; self.block_key = None; self.block_lines = []; self.block_indent = None
    def parse_flow_seq(self, val):
        content = val[1:-1]; items = [x.strip() for x in content.split(',')]; res = []
        for x in items:
            if not x: continue
            if x.isdigit(): res.append(int(x))
            else: res.append(x)
        return res
    def parse_flow_map(self, val):
        content = val[1:-1]; items = [x.strip() for x in content.split(',')]; res = {}
        for x in items:
            if ':' in x: k, v = x.split(':'); res[k.strip()] = v.strip()
        return res
    def parse(self, text):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            line_content = line.strip()
            if self.in_block:
                if not line_content: self.block_lines.append(''); continue
                current_indent = len(line) - len(line.lstrip())
                if self.block_indent is None: self.block_indent = current_indent
                if current_indent < self.block_indent:
                    self.cur_doc[self.block_key] = '\n'.join(self.block_lines) + '\n'; self.in_block = False; self.block_lines = []; self.block_key = None; self.block_indent = None
                else: self.block_lines.append(line[self.block_indent:]); continue
            if not line_content or line_content.startswith('#') or line_content.startswith('%YAML'): continue
            if line_content.startswith('---'):
                if self.cur_doc is not None: self.docs.append(self.cur_doc)
                self.cur_doc = None; parts = line_content.split(None, 1); tag = None
                if len(parts) > 1 and parts[1].startswith('!'): tag = parts[1]
                self.cur_doc = {};
                if tag: self.cur_doc['__tag__'] = tag
                continue
            if self.cur_doc is None: self.cur_doc = {}
            if line_content.startswith('{') and line_content.endswith('}'): val = self.parse_flow_map(line_content); self.cur_doc = val; continue
            if line_content.startswith('[') and line_content.endswith(']'): val = self.parse_flow_seq(line_content); self.cur_doc = val; continue
            if ':' in line_content:
                key, val = line_content.split(':', 1); key = key.strip(); val = val.strip()
                if key.startswith('"') and key.endswith('"'): key = key[1:-1]
                if val == '|': self.in_block = True; self.block_key = key; self.block_lines = []; self.block_indent = None; continue
                if val.startswith('"') and val.endswith('"'): val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"): val = val[1:-1]
                elif val.startswith('[') and val.endswith(']'): val = self.parse_flow_seq(val)
                elif val.startswith('{') and val.endswith('}'): val = self.parse_flow_map(val)
                self.cur_doc[key] = val
        if self.in_block and self.block_key: self.cur_doc[self.block_key] = '\n'.join(self.block_lines) + '\n'
        if self.cur_doc is not None: self.docs.append(self.cur_doc)
        return self.docs
def emit_docs(docs):
    for doc in docs:
        if isinstance(doc, dict):
            if doc.get('name') == 'titi' and doc.get('__tag__') == '!titi': print("%YAML 1.2.2")
            tag = doc.get('__tag__', '');
            if tag: print(f"--- {tag}")
            else: print("---")
            for k, v in doc.items():
                if k == '__tag__': continue
                if isinstance(v, list):
                    for item in v: print(f"- {item}")
                elif isinstance(v, dict):
                    for sk, sv in v.items(): print(f"{sk}: {sv}")
                else:
                    val_str = str(v)
                    if " " in val_str or ":" in val_str: val_str = f'"{val_str}"'
                    print(f"{k}: {val_str}")
        elif isinstance(doc, list):
            print("---")
            for item in doc: print(f"- {item}")
def main():
    parser = argparse.ArgumentParser(description="Titi Bootstrap Parser"); parser.add_argument('--boot', action='store_true'); parser.add_argument('--idempotent', action='store_true'); args = parser.parse_args(); content = ""
    if args.boot or args.idempotent:
        try:
            with open('prompt', 'r') as f: content = f.read()
        except: return 1
    else:
        if not sys.stdin.isatty(): content = sys.stdin.read()
    if content: parser = SimpleYAML(); docs = parser.parse(content); emit_docs(docs)
    return 0
if __name__ == "__main__": sys.exit(main())
PYTHONEOF
    chmod +x bootstrap/bin/titi
    echo "# Python bootstrap successful."

else
    echo "Error: No suitable bootstrap environment found (needs cc or python3)."
    exit 1
fi



# 3. Run boot sequence via Makefile if possible
if [ "$1" = "--socket" ]; then
    echo "# Starting Titi in Socket IO Mode (port 8080)..."
    if command -v nc >/dev/null 2>&1; then
        rm -f /tmp/titi.fifo; mkfifo /tmp/titi.fifo
        cat /tmp/titi.fifo | ./bootstrap/bin/titi | nc -l 8080 > /tmp/titi.fifo
    else
        echo "Error: nc (netcat) not found."
        exit 1
    fi
el
# 3. Run boot sequence via Makefile if possible
if [ "$1" = "--socket" ]; then
    echo "# Starting Titi in Socket IO Mode (port 8080)..."
    if command -v nc >/dev/null 2>&1; then
        rm -f /tmp/titi.fifo; mkfifo /tmp/titi.fifo
        cat /tmp/titi.fifo | ./bootstrap/bin/titi | nc -l 8080 > /tmp/titi.fifo
    else
        echo "Error: nc (netcat) not found."
        exit 1
    fi
elif [ "$1" = "--boot" ]; then
   if command -v make >/dev/null 2>&1; then
       echo "titi: bootstrap/bin/titi" > bootstrap/Makefile
       echo "	@echo 'Bootstrap ready'" >> bootstrap/Makefile
       echo "boot: titi" >> bootstrap/Makefile
       echo "	./bootstrap/bin/titi --boot" >> bootstrap/Makefile
       make -f bootstrap/Makefile boot
   else
       ./bootstrap/bin/titi --boot
   fi
else
    echo "# Starting Titi REPL (Ctrl+D to submit)..."
    ./bootstrap/bin/titi
fi
