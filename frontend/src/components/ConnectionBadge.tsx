interface QueryLike {
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
}

interface Props {
  query: QueryLike;
}

export default function ConnectionBadge({ query }: Props) {
  if (query.isLoading) {
    return (
      <span style={{ padding: "4px 12px", borderRadius: 20, background: "#1e293b", color: "#94a3b8", fontSize: 12, fontWeight: 600 }}>
        ⏳ Connecting...
      </span>
    );
  }
  if (query.isError) {
    return (
      <span style={{ padding: "4px 12px", borderRadius: 20, background: "#450a0a", color: "#f87171", fontSize: 12, fontWeight: 600 }}>
        ✗ Not Connected
      </span>
    );
  }
  if (query.isSuccess) {
    return (
      <span style={{ padding: "4px 12px", borderRadius: 20, background: "#052e16", color: "#4ade80", fontSize: 12, fontWeight: 600 }}>
        ✓ Connected to Salesforce
      </span>
    );
  }
  return null;
}
