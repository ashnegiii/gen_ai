import { Toaster } from '@/components/ui/sonner';
import type { Metadata } from 'next';
import { Geist, Geist_Mono, Nunito } from 'next/font/google';
import './globals.css';

const nunitoSans = Nunito({
	subsets: ['latin'],
	variable: '--font-sans',
});

const geistSans = Geist({
	subsets: ['latin'],
	variable: '--font-geist-sans',
});

const geistMono = Geist_Mono({
	subsets: ['latin'],
	variable: '--font-geist-mono',
});

export const metadata: Metadata = {
	title: 'Chadoc - Document Chat AI for customer service (CS) use cases',
	description: 'Chat with your documents using AI',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html
			lang='en'
			className={nunitoSans.variable}
		>
			<body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
				{children}
				<Toaster />
			</body>
		</html>
	);
}
