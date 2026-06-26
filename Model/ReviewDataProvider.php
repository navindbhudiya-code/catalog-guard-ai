<?php
/**
 * UI-component data provider for the Review Fixes grid.
 *
 * Backs the admin grid with pending fix proposals fetched live from the
 * CatalogGuard Python service (no local DB table). Lives under Model/ rather
 * than Ui/ to avoid a case collision with the project's lowercase ui/ folder
 * on case-insensitive filesystems.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Model;

use Magento\Ui\DataProvider\AbstractDataProvider;

class ReviewDataProvider extends AbstractDataProvider
{
    private PythonService $service;
    private int $page = 1;
    private int $size = 50;

    /**
     * @param array<string, mixed> $meta
     * @param array<string, mixed> $data
     */
    public function __construct(
        string $name,
        string $primaryFieldName,
        string $requestFieldName,
        PythonService $service,
        array $meta = [],
        array $data = []
    ) {
        parent::__construct($name, $primaryFieldName, $requestFieldName, $meta, $data);
        $this->service = $service;
    }

    /**
     * The grid passes (currentPage, pageSize); remember it for paging.
     */
    public function setLimit($offset, $size): void
    {
        $this->page = max(1, (int) $offset);
        $this->size = max(1, (int) $size);
    }

    /**
     * @return array{items: array<int, array<string, mixed>>, totalRecords: int}
     */
    public function getData(): array
    {
        try {
            $result = $this->service->getPendingProposals($this->page, $this->size);
        } catch (\Throwable) {
            return ['items' => [], 'totalRecords' => 0];
        }

        return [
            'items' => $result['items'],
            'totalRecords' => $result['totalRecords'],
        ];
    }
}
