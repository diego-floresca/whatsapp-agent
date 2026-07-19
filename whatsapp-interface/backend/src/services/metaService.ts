import axios from 'axios';

const META_VERSION = 'v25.0';

export async function sendWhatsAppMessage(toNumber: string, body: string): Promise<void> {
  const token = process.env.META_ACCESS_TOKEN;
  const phoneNumberId = process.env.PHONE_NUMBER_ID;

  if (!token || !phoneNumberId) {
    throw new Error('META_ACCESS_TOKEN o PHONE_NUMBER_ID no configurados');
  }

  const url = `https://graph.facebook.com/${META_VERSION}/${phoneNumberId}/messages`;

  await axios.post(
    url,
    {
      messaging_product: 'whatsapp',
      to: toNumber,
      type: 'text',
      text: { body },
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
}
