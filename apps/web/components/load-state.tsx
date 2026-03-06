type LoadStateProps = {
  loading: boolean;
  error?: string | null;
  empty?: string | null;
};

export function LoadState({ loading, error, empty }: LoadStateProps) {
  if (loading) {
    return <div className="note">Loading current backend state…</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (empty) {
    return <div className="empty">{empty}</div>;
  }

  return null;
}
