package io.pealang.client;
import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
class PeaLangClientTest {
 @Test void clientTypeLoads(){ assertNotNull(PeaLangClient.class); }
 @Test void exceptionTypeLoads(){ assertTrue(RuntimeException.class.isAssignableFrom(PeaLangException.class)); }
 @Test void clientSurfaceIsDeclared() throws Exception {
  for (String name : new String[]{"health","ready"}) assertNotNull(PeaLangClient.class.getMethod(name));
  for (String name : new String[]{"compile","loadModule","invoke"}) assertNotNull(PeaLangClient.class.getMethod(name,String.class));
 }
}
