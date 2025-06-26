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