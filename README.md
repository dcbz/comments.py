comments.py
===========

Comments.py plugin for lldb to display disassembly with user defined comments.

(lldb) command script import ~/comments.py/comments.py
--------------------------------------
 Commented Disassembly lldb Module
 nemo 2014
--------------------------------------

(lldb) cdis 0x7fff90f549f2
0x00007fff90f549e8      movl    $0x2000003, %eax
0x00007fff90f549ed      movq    %rcx, %r10
0x00007fff90f549f0      syscall 
0x00007fff90f549f2      jae     0x7fff90f549fc  // read + 20
0x00007fff90f549f4      movq    %rax, %rdi
0x00007fff90f549f7      jmpq    0x7fff90f5019a  // cerror
0x00007fff90f549fc      ret
0x00007fff90f549fd      nop
0x00007fff90f549fe      nop
0x00007fff90f549ff      nop
(lldb) add_comment 0x00007fff90f549f0 "syscall for read"                                                                                                                                                                             (lldb) cdis 0x7fff90f549f2
0x00007fff90f549e8      movl    $0x2000003, %eax
0x00007fff90f549ed      movq    %rcx, %r10
0x00007fff90f549f0      syscall          //syscall for read
0x00007fff90f549f2      jae     0x7fff90f549fc  // read + 20
0x00007fff90f549f4      movq    %rax, %rdi
0x00007fff90f549f7      jmpq    0x7fff90f5019a  // cerror
0x00007fff90f549fc      ret
0x00007fff90f549fd      nop
0x00007fff90f549fe      nop
0x00007fff90f549ff      nop
(lldb) save_comment_db ~/awesomecomments.db
(lldb) load_comment_db ~/awesomecomments.db
(lldb) 

