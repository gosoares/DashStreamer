export const capitalizeStatus = (status) => {
  return status.charAt(0).toUpperCase() + status.slice(1);
};

export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(date);
};

export const formatBitrate = (bitrateInput) => {
  if (!bitrateInput || bitrateInput === 'N/A') return 'N/A';

  // Handle different input formats
  let bitrateBps;
  if (typeof bitrateInput === 'string') {
    // Handle "5120k" format
    if (bitrateInput.endsWith('k')) {
      bitrateBps = parseInt(bitrateInput) * 1000;
    } else {
      bitrateBps = parseInt(bitrateInput);
    }
  } else {
    bitrateBps = parseInt(bitrateInput);
  }

  if (isNaN(bitrateBps) || bitrateBps <= 0) return 'N/A';

  // Convert to kbps and Mbps
  const bitrateKbps = bitrateBps / 1000;
  const bitrateMbps = bitrateKbps / 1024;

  if (bitrateMbps >= 1) {
    // Show as Mbps, remove .0 if it's a whole number
    const formatted = bitrateMbps.toFixed(1);
    return formatted.endsWith('.0') ? `${Math.round(bitrateMbps)} Mbps` : `${formatted} Mbps`;
  } else {
    // Show as kbps, remove .0 if it's a whole number
    const formatted = bitrateKbps.toFixed(1);
    return formatted.endsWith('.0') ? `${Math.round(bitrateKbps)} kbps` : `${formatted} kbps`;
  }
};
