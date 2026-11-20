async function saveToVault(payload) {
  const response = await fetch('feedback', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  });
  const receipt = await response.json();
  if (!response.ok) {
    const error = new Error(receipt.error || '知识库未能保存反馈。');
    error.status = response.status;
    throw error;
  }
  if (!Number.isInteger(receipt.saved) || !Number.isInteger(receipt.duplicates) ||
      !Number.isInteger(receipt.historical_only) || receipt.saved + receipt.duplicates !== payload.entries.length) {
    throw new Error('尚未收到完整的保存回执。');
  }
  return receipt;
}
