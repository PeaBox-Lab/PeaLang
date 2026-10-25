

package io.pealang.client;
import java.net.URI;import java.net.http.*;import java.time.Duration;import java.io.IOException;
public final class PeaLangClient {
 private final HttpClient client; private final URI base;
 public PeaLangClient(String baseUrl){base=URI.create(baseUrl);client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();}
 public String health() throws IOException,InterruptedException{return get("/health");}
 public String ready() throws IOException,InterruptedException{return get("/ready");}
 public String compile(String json) throws IOException,InterruptedException{return post("/v1/compile",json);}
 public String loadModule(String json) throws IOException,InterruptedException{return post("/v1/modules/load",json);}
 public String invoke(String json) throws IOException,InterruptedException{return post("/v1/invoke",json);}
 private String get(String p)throws IOException,InterruptedException{return send(HttpRequest.newBuilder(base.resolve(p)).GET().build());}
 private String post(String p,String json)throws IOException,InterruptedException{return send(HttpRequest.newBuilder(base.resolve(p)).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(json)).build());}
 private String send(HttpRequest r)throws IOException,InterruptedException{var res=client.send(r,HttpResponse.BodyHandlers.ofString());if(res.statusCode()/100!=2)throw new PeaLangException(res.statusCode(),res.body());return res.body();}
}


