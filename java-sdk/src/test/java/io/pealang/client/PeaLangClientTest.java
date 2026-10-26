package io.pealang.client;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
class PeaLangClientTest { @Test void clientTypeLoads(){ assertNotNull(PeaLangClient.class); } @Test void exceptionTypeLoads(){ assertTrue(RuntimeException.class.isAssignableFrom(PeaLangException.class)); } }
