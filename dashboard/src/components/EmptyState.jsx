export default function EmptyState({ children = 'Nothing to display.' }) {
  return <p className="empty" role="status">{children}</p>
}
