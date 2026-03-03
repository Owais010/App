import { useState } from 'react'
import { Plus, Link as LinkIcon, Edit2, Trash2, GripVertical } from 'lucide-react'
import Button from '../../components/Button'

export default function LearningResourcesManager() {
    const [resources, setResources] = useState([
        { id: 1, title: 'Introduction to React Hooks', type: 'video', topic: 'Frontend', priority: 1, source: 'YouTube' },
        { id: 2, title: 'Basic Geometry Rules', type: 'article', topic: 'Geometry', priority: 2, source: 'Khan Academy' },
        { id: 3, title: 'Solving Linear Equations', type: 'interactive', topic: 'Algebra', priority: 1, source: 'Internal' }
    ])

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-heading font-bold text-surface-900 dark:text-white">
                        Learning Resources
                    </h1>
                    <p className="text-surface-500 dark:text-surface-400 mt-1">
                        Curate playlists and articles for adaptation loops
                    </p>
                </div>

                <Button className="flex items-center gap-2">
                    <Plus size={18} /> Add Resource
                </Button>
            </div>

            <div className="bg-white dark:bg-surface-900 border border-surface-200 dark:border-white/[0.08] rounded-2xl overflow-hidden">
                <div className="p-4 border-b border-surface-200 dark:border-white/[0.08] bg-surface-50 dark:bg-surface-800/50">
                    <h2 className="font-semibold text-surface-700 dark:text-surface-300">Active Materials (Drag to re-order priority)</h2>
                </div>

                <div className="divide-y divide-surface-200 dark:divide-white/[0.08]">
                    {resources.map((res) => (
                        <div key={res.id} className="flex items-center gap-4 p-4 hover:bg-surface-50 dark:hover:bg-white/[0.02] transition-colors group">
                            <div className="cursor-grab text-surface-300 hover:text-surface-500">
                                <GripVertical size={20} />
                            </div>

                            <div className="w-10 h-10 rounded-lg bg-surface-100 dark:bg-surface-800 flex items-center justify-center text-primary flex-shrink-0">
                                <LinkIcon size={18} />
                            </div>

                            <div className="flex-1 min-w-0">
                                <h4 className="font-medium text-surface-900 dark:text-white truncate">{res.title}</h4>
                                <div className="flex items-center gap-3 mt-1 text-xs text-surface-500 dark:text-surface-400">
                                    <span className="capitalize">{res.type}</span>
                                    <span>•</span>
                                    <span>{res.topic}</span>
                                    <span>•</span>
                                    <span>{res.source}</span>
                                </div>
                            </div>

                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button className="p-2 text-surface-400 hover:text-primary rounded-lg transition-colors">
                                    <Edit2 size={16} />
                                </button>
                                <button className="p-2 text-surface-400 hover:text-red-500 rounded-lg transition-colors">
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
