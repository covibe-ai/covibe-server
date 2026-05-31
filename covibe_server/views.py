from django.http import JsonResponse


async def healthcheck(request):
    return JsonResponse({'status': 'ok'}, status=200)
