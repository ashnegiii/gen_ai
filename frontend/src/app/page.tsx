'use client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { FileText, Loader2, Trash2, Upload } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

import { toast } from 'sonner';

interface Document {
	id: string;
	name: string;
	uploadedAt: string;
	size: string;
}

export default function Home() {
	const [documents, setDocuments] = useState<Document[]>([]);
	const [loading, setLoading] = useState(true);
	const [uploading, setUploading] = useState(false);
	const [deletingId, setDeletingId] = useState<string | null>(null);


	const fetchDocuments = async () => {
        try {
            const response = await fetch('http://localhost:5001/api/documents');
            if (!response.ok) throw new Error('Failed to fetch documents');
            const data = await response.json();
            setDocuments(data.documents);
        } catch (error) {
            console.error(error);
            toast.error('Error', { description: 'Could not load documents from server.' });
        } finally {
            setLoading(false);
        }
    };

	useEffect(() => {
        fetchDocuments();
    }, []);

	const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (!file) return;

		setUploading(true);

		try {
			const formData = new FormData();
			formData.append('file', file);

			// Upload
			const response = await fetch('http://localhost:5001/api/upload', {
				method: 'POST',
				body: formData,
			});

			if (!response.ok) throw new Error('Upload failed');

			const data = await response.json();

			// Add to documents list
			const newDoc: Document = {
				id: data.id || Date.now().toString(),
				name: file.name,
				uploadedAt: new Date().toLocaleString('en-US', {
					year: 'numeric',
					month: '2-digit',
					day: '2-digit',
					hour: '2-digit',
					minute: '2-digit',
				}),
				size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
			};
			setDocuments([newDoc, ...documents]);

			toast.success('Upload successful', {
				description: `${file.name} has been uploaded successfully.`,
			});
		} catch (error) {
			toast.error('Upload failed', {
				description: 'Failed to upload document. Please try again.',
			});
		} finally {
			setUploading(false);
			e.target.value = '';
		}
	};

	const handleDelete = async (id: string, name: string) => {
		setDeletingId(id);

		try {
			const response = await fetch('http://localhost:5001/api/documents', {
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ id }),
			});

			if (!response.ok) throw new Error('Delete failed');

			setDocuments(documents.filter((doc) => doc.id !== id));

			toast('Document deleted', { description: `${name} has been deleted.` });
		} catch (error) {
			toast.error('Delete failed', {
				description: 'Failed to delete document. Please try again.',
			});
		} finally {
			setDeletingId(null);
		}
	};

	return (
		<div className='min-h-screen bg-background'>
			<header className='border-b border-border shrink-0'>
				<div className='container mx-auto px-4 py-4'>
					<nav className='flex items-center justify-between'>
						<div className='flex items-center gap-8'>
							<h1 className='text-xl font-semibold'>Chadoc</h1>
							<div className='flex gap-6 text-sm'>
								<Link
									href='/'
									className='text-foreground font-medium'
								>
									Documents
								</Link>
								<Link
									href='/chat'
									className='text-muted-foreground hover:text-foreground transition-colors'
								>
									Chat
								</Link>
							</div>
						</div>
					</nav>
				</div>
			</header>
			<main className='container mx-auto px-4 py-12'>
				<div className='max-w-4xl mx-auto space-y-8'>
					<div>
						<h2 className='text-3xl font-semibold mb-2'>Document Management</h2>
						<p className='text-muted-foreground'>Upload and manage your documents for RAG-powered chat for customer service (CS) use cases</p>
					</div>
					<Card>
						<CardHeader>
							<CardTitle>Upload Document</CardTitle>
							<CardDescription>Upload a document to add it to your knowledge base</CardDescription>
						</CardHeader>
						<CardContent>
							<Label htmlFor='file-upload'>
								<div className='w-full border-2 border-dashed border-border rounded-lg p-12 text-center hover:border-muted-foreground transition-colors cursor-pointer'>
									{uploading ? (
										<div className='flex flex-col items-center gap-3'>
											<Loader2 className='h-10 w-10 text-muted-foreground animate-spin' />
											<p className='text-sm text-muted-foreground'>Uploading...</p>
										</div>
									) : (
										<div className='flex flex-col items-center gap-3'>
											<Upload className='h-10 w-10 text-muted-foreground' />
											<div>
												<p className='text-sm font-medium mb-1'>
													Click to upload or drag and drop
												</p>
												<p className='text-xs text-muted-foreground'>CSV (max 10MB)</p>
											</div>
										</div>
									)}
								</div>
								<input
									id='file-upload'
									type='file'
									className='sr-only'
									onChange={handleFileUpload}
									disabled={uploading}
									accept='.csv'
								/>
							</Label>
						</CardContent>
					</Card>

					<Card>
						<CardHeader>
							<CardTitle>Your Documents</CardTitle>
							<CardDescription>
								{documents.length} document{documents.length !== 1 ? 's' : ''} in your knowledge base
							</CardDescription>
						</CardHeader>
						<CardContent>
							{documents.length === 0 ? (
								<div className='text-center py-12 text-muted-foreground'>
									<FileText className='h-12 w-12 mx-auto mb-3 opacity-50' />
									<p>No documents uploaded yet</p>
								</div>
							) : (
								<div className='space-y-3'>
									{documents.map((doc) => (
										<div
											key={doc.id}
											className='flex items-center justify-between p-4 border border-border rounded-lg hover:bg-accent/50 transition-colors'
										>
											<div className='flex items-center gap-3 flex-1 min-w-0'>
												<FileText className='h-5 w-5 text-muted-foreground shrink-0' />
												<div className='min-w-0 flex-1'>
													<p className='font-medium truncate'>{doc.name}</p>
													<p className='text-xs text-muted-foreground'>
														{doc.uploadedAt} • {doc.size}
													</p>
												</div>
											</div>
											<Button
												variant='ghost'
												size='sm'
												onClick={() => handleDelete(doc.id, doc.name)}
												disabled={deletingId === doc.id}
												className='shrink-0 ml-2'
											>
												{deletingId === doc.id ? (
													<Loader2 className='h-4 w-4 animate-spin' />
												) : (
													<Trash2 className='h-4 w-4' />
												)}
											</Button>
										</div>
									))}
								</div>
							)}
						</CardContent>
					</Card>
				</div>
			</main>
		</div>
	);
}
