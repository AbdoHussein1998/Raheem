import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <main className="flex-grow pt-28 text-center px-margin-mobile">
      <h1 className="text-headline-lg font-bold text-primary">الصفحة غير موجودة</h1>
      <Link to="/" className="text-surface-tint underline">العودة للرئيسية</Link>
    </main>
  );
}
