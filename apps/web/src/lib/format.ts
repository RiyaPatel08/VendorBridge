export function roleLabel(role: string): string {
  return role
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function stageLabel(stage: string): string {
  return roleLabel(stage);
}

export function shortHash(value: string): string {
  return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

