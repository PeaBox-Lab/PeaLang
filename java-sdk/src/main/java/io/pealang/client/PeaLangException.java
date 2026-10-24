package io.pealang.client; public final class PeaLangException extends RuntimeException { public final int status; public PeaLangException(int status,String body){super(body);this.status=status;} }
