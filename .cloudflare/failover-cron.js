export default {
  async scheduled(event, env, ctx) {
    // Define maps of environemnt variables
    const endpoints = [env.PRIMARY_HEALTH_ENDPOINT, env.SECONDARY_HEALTH_ENDPOINT];
    const renders = ['ar-ems-l6.onrender.com', 'ar-ems-l6-test.onrender.com'];
    const record_ids = [env.PRIMARY_RECORD_ID, env.SECONDARY_RECORD_ID];

    const tunnel = `${env.TUNNEL_UUID}.cfargotunnel.com`;
    const headers = {
      Authorization: `Bearer ${env.CF_API_TOKEN}`,
      "Content-Type": "application/json",
    };

    for (let i = 0; i < record_ids.length; i++){
      const record = record_ids[i];
      const endpoint = endpoints[i];
      const render = renders[i];
      const api = `https://api.cloudflare.com/client/v4/zones/${env.ZONE_ID}/dns_records/${record}`;
      
      let healthy = false;

      try {
        const r = await fetch(
          endpoint,
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
    }
  },
};