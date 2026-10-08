export function isValidVin(vin) {
  if (typeof vin !== 'string') return false;
  const trimmed = vin.trim();
  if (trimmed.length !== 17) return false;
  return /^(?:[A-HJ-NPR-Z0-9]{17})$/i.test(trimmed);
}

export async function decodeVin(vin) {
  const url = `https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/${encodeURIComponent(vin)}?format=json`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`NHTSA request failed with status ${response.status}`);
  }

  const payload = await response.json();

  return {
    count: payload.Count ?? 0,
    message: payload.Message ?? '',
    results: payload.Results ?? []
  };
}
