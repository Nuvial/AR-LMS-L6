export default {
  async scheduled(event, env, ctx) {
    const tunnel = `${env.TUNNEL_UUID}.cfargotunnel.com`;
    const render = "ar-ems-l6.onrender.com";
    const api = `https://api.cloudflare.com/client/v4/zones/${env.ZONE_ID}/dns_records/${env.RECORD_ID}`;
    const headers = {
      Authorization: `Bearer ${env.CF_API_TOKEN}`,
      "Content-Type": "application/json",
    };

    let healthy = false;
    try {
      const r = await fetch(
        "https://ar-ems-l6-primary.nuvial.win/ping",
        { signal: AbortSignal.timeout(8000) }
      );
      healthy = r.ok;
    } catch { 
      healthy = false; 
    }

    const want = healthy ? tunnel : render;
    const proxied = healthy;
    const ttl = proxied ? 1 : 60;
    const cur = await fetch(api, { headers }).then((r) => r.json());

    if (cur.result.content !== want || cur.result.proxied !== proxied) {
      await fetch(api, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ content: want, proxied, ttl }),
      });
    }
  },
};